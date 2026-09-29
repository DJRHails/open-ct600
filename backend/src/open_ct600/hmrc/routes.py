"""HMRC filing API: check a return against HMRC's rules, download its XML, submit it to HMRC.

``POST /api/returns/validate`` and ``POST /api/returns/ct600.xml`` take ``ReturnRequest``;
``POST /api/returns/submit-to-hmrc`` takes ``SubmitRequest`` and answers with HMRC's receipt
or rejection, or an HTTP error whose ``detail`` is ``{"error", "message", "correlation_id",
"errors"}`` (see ``_FAILURES``).
"""

import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import httpx2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from lxml import etree
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from starlette.concurrency import run_in_threadpool

from open_ct600.config import Settings
from open_ct600.ct600 import (
    CT600Return,
    Declaration,
    ReturnComputation,
    SignatoryCapacity,
    compute_return,
)
from open_ct600.hmrc.client import (
    AuthenticationFailedError,
    BusinessErrors,
    PollTimeoutError,
    ProcessingFailedError,
    SubmissionTooLargeError,
    TransactionEngineClient,
    TransactionEngineError,
)
from open_ct600.hmrc.govtalk import (
    Environment,
    GatewayCredentials,
    GovTalkError,
    Receipt,
    Vendor,
    build_submission,
)
from open_ct600.hmrc.validate import Problem, validate_return
from open_ct600.hmrc.xml import build_return_xml
from open_ct600.hmrc.xmldoc import serialise
from open_ct600.schema.spec import PAGE_DEFINITIONS, RETURN_PATH, PageCode, load_spec

PRODUCT = "Open CT600"
PRODUCT_VERSION = "0.1.0"
POLL_TIMEOUT_SECONDS = 120.0

_HMRC_LOCATION_NOISE = re.compile(
    r"""(?x)
    (?<=/) [A-Za-z]+ :   # the namespace prefix HMRC puts on each step, such as ct:
    | \[ [0-9]+ \]       # a positional predicate such as [1]
    """
)
_PAGE_BY_ELEMENT: dict[str, PageCode] = {page.element: page.code for page in PAGE_DEFINITIONS}


class _Request(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReturnRequest(_Request):
    """A return to check or download.

    Attributes:
        declaration: Who will declare it (boxes 975 and 985). Before the declaration is made,
            the signing director is used, in the capacity of director.
    """

    ct600: CT600Return
    declaration: Declaration | None = None


class SubmitRequest(_Request):
    """A declared return to send to HMRC with the company's Government Gateway credentials.

    Attributes:
        environment: ``test-in-live`` has HMRC check everything without filing the return;
            ``live`` files it.
        gateway_user_id: The company's Government Gateway user ID.
        gateway_password: Its password: used for this submission only, never stored or logged.
    """

    ct600: CT600Return
    declaration: Declaration
    environment: Literal["test-in-live", "live"]
    gateway_user_id: Annotated[str, Field(min_length=1, max_length=64)]
    gateway_password: Annotated[SecretStr, Field(min_length=1)]


class ReturnProblem(BaseModel):
    """Something HMRC would reject, located on the form.

    Attributes:
        code: HMRC's error code (4000-4999 schema, 5004/5005/9xxx business rules).
        message: HMRC's message.
        box: The box at fault, when the element is a box (``"475"``, ``"A15"``).
        page: The supplementary page it is on (``"A"``), or ``None`` for the main return.
        path: The element at fault, like ``/IRenvelope/CompanyTaxReturn/Declaration/Name``.
    """

    code: int
    message: str
    box: str | None
    page: PageCode | None
    path: str | None


class ValidationReport(BaseModel):
    """The result of checking a return against HMRC's schema and business rules.

    Attributes:
        valid: Whether HMRC's schema and rules accept the return.
        documents_attached: Whether the iXBRL accounts and computations could be attached.
            Until they are, HMRC's rules report 9113 and 9965 (no accounts, no computations).
        problems: Everything to fix, in document order.
    """

    valid: bool
    documents_attached: bool
    problems: list[ReturnProblem]


class HMRCError(BaseModel):
    """One error from HMRC, located on the form where HMRC says where."""

    number: int | None
    type: str
    message: str
    box: str | None
    page: PageCode | None
    location: str


class HMRCReceipt(BaseModel):
    """HMRC accepted the return (``test-in-live``: would have accepted it).

    Attributes:
        irmark: The IRmark HMRC computed (Base64), equal to the one sent.
        irmark_base32: The same digest as HMRC quotes it on receipts.
        receipt_xml: HMRC's signed response, for the company's records.
    """

    status: Literal["accepted"] = "accepted"
    environment: str
    correlation_id: str
    irmark: str | None
    irmark_base32: str
    accepted_time: datetime | None
    messages: list[str]
    receipt_xml: str


class HMRCRejection(BaseModel):
    """HMRC rejected the return's content (error 3001): correct it and submit again."""

    status: Literal["rejected"] = "rejected"
    environment: str
    correlation_id: str
    errors: list[HMRCError]


@dataclass(frozen=True)
class IXBRLDocuments:
    """The iXBRL accounts and computations filed with a return."""

    accounts: str
    computations: str


type IXBRLRenderer = Callable[[CT600Return, ReturnComputation], IXBRLDocuments | None]


def _render_ixbrl(ct600: CT600Return, computation: ReturnComputation) -> IXBRLDocuments | None:
    """Render the return's iXBRL documents; ``None`` while the renderers are unavailable."""
    return None


def ixbrl_renderer() -> IXBRLRenderer:
    """Dependency: the function that renders a return's iXBRL documents."""
    return _render_ixbrl


async def http_client() -> AsyncIterator[httpx2.AsyncClient]:
    """Dependency: an HTTP client for one exchange with HMRC."""
    async with httpx2.AsyncClient(timeout=httpx2.Timeout(60.0)) as client:
        yield client


_FAILURES: tuple[tuple[type[TransactionEngineError], int, str], ...] = (
    (AuthenticationFailedError, status.HTTP_401_UNAUTHORIZED, "authentication_failed"),
    (SubmissionTooLargeError, status.HTTP_413_CONTENT_TOO_LARGE, "too_large"),
    (ProcessingFailedError, status.HTTP_503_SERVICE_UNAVAILABLE, "hmrc_processing_failed"),
    (PollTimeoutError, status.HTTP_504_GATEWAY_TIMEOUT, "hmrc_timeout"),
    (TransactionEngineError, status.HTTP_502_BAD_GATEWAY, "hmrc_error"),
)
"""HMRC failures → HTTP status and ``detail.error``, first match wins."""


def hmrc_router(settings: Settings) -> APIRouter:
    """Build the HMRC filing routes for a deployment's settings."""
    router = APIRouter(prefix="/api/returns", tags=["hmrc"])
    router.add_api_route("/validate", check_return, methods=["POST"])
    router.add_api_route("/ct600.xml", download_xml, methods=["POST"], response_class=Response)

    async def submit_to_hmrc(
        request: SubmitRequest,
        http: Annotated[httpx2.AsyncClient, Depends(http_client)],
        render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)],
    ) -> HMRCReceipt | HMRCRejection:
        """Submit a declared return to HMRC and return HMRC's answer."""
        return await _submit(settings, request, http, render)

    router.add_api_route("/submit-to-hmrc", submit_to_hmrc, methods=["POST"])
    return router


def check_return(
    request: ReturnRequest, render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)]
) -> ValidationReport:
    """Check a return against HMRC's CT600 schema and business rules, offline."""
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    envelope = _envelope(request.ct600, computation, _declaration(request), documents)
    problems = [_located(problem) for problem in validate_return(envelope)]
    return ValidationReport(
        valid=not problems, documents_attached=documents is not None, problems=problems
    )


def download_xml(
    request: ReturnRequest, render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)]
) -> Response:
    """Download the return's CT600 XML (the ``IRenvelope``, with iXBRL when available)."""
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    envelope = _envelope(request.ct600, computation, _declaration(request), documents)
    company, period = request.ct600.company, request.ct600.period
    filename = f"ct600-{company.utr}-{period.end.isoformat()}.xml"
    return Response(
        content=serialise(envelope),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _submit(
    settings: Settings,
    request: SubmitRequest,
    http: httpx2.AsyncClient,
    render: IXBRLRenderer,
) -> HMRCReceipt | HMRCRejection:
    vendor = _vendor(settings)
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    if documents is None:
        raise _failure(
            status.HTTP_409_CONFLICT,
            "ixbrl_unavailable",
            "HMRC needs the company's accounts and tax computations in iXBRL with the return, "
            "and this service cannot produce them yet, so the return cannot be submitted.",
        )
    envelope = _envelope(request.ct600, computation, request.declaration, documents)
    problems = await run_in_threadpool(validate_return, envelope)
    if problems:
        raise _invalid(problems)
    environment = Environment(request.environment)
    credentials = GatewayCredentials(
        user_id=request.gateway_user_id, password=request.gateway_password
    )
    message, irmark = build_submission(
        envelope, environment=environment, vendor=vendor, credentials=credentials
    )
    client = TransactionEngineClient(environment, http=http, max_wait=POLL_TIMEOUT_SECONDS)
    try:
        outcome = await client.submit(message)
    except TransactionEngineError as error:
        raise _hmrc_failure(error) from None
    if isinstance(outcome, BusinessErrors):
        return HMRCRejection(
            environment=environment,
            correlation_id=outcome.correlation_id,
            errors=[_hmrc_error(error) for error in outcome.errors],
        )
    return _receipt(outcome, environment, irmark.base32)


def _vendor(settings: Settings) -> Vendor:
    if not settings.hmrc_submission_enabled or settings.hmrc_vendor_id is None:
        raise _failure(
            status.HTTP_403_FORBIDDEN,
            "submission_disabled",
            "Submitting to HMRC is switched off on this service. Whoever runs it needs an HMRC "
            "vendor ID (HMRC_VENDOR_ID) and to allow submissions (HMRC_SUBMISSION_ENABLED=true). "
            "You can still download the return and file it another way.",
        )
    return Vendor(vendor_id=settings.hmrc_vendor_id, product=PRODUCT, version=PRODUCT_VERSION)


def _declaration(request: ReturnRequest) -> Declaration:
    if request.declaration is not None:
        return request.declaration
    return Declaration(
        name=request.ct600.accounts.signing_director,
        capacity=SignatoryCapacity.DIRECTOR,
        confirmed=True,
    )


def _envelope(
    ct600: CT600Return,
    computation: ReturnComputation,
    declaration: Declaration,
    documents: IXBRLDocuments | None,
) -> etree._Element:
    return build_return_xml(
        ct600,
        computation,
        declaration=declaration,
        accounts_xhtml=documents.accounts if documents else None,
        computations_xhtml=documents.computations if documents else None,
    )


def _receipt(receipt: Receipt, environment: Environment, irmark_base32: str) -> HMRCReceipt:
    return HMRCReceipt(
        environment=environment,
        correlation_id=receipt.correlation_id,
        irmark=receipt.irmark,
        irmark_base32=irmark_base32,
        accepted_time=receipt.accepted_time,
        messages=list(receipt.messages),
        receipt_xml=receipt.response.decode("utf-8"),
    )


def _located(problem: Problem) -> ReturnProblem:
    return ReturnProblem(
        code=problem.code,
        message=problem.message,
        box=problem.box,
        page=_page(problem.path),
        path=problem.path,
    )


def _hmrc_error(error: GovTalkError) -> HMRCError:
    path = _form_path(error.location)
    box = None
    if path is not None:
        try:
            box = load_spec().node(path).box
        except LookupError:
            box = None  # HMRC located it outside the schema's boxes (header, attachments).
    return HMRCError(
        number=error.number,
        type=error.error_type,
        message=error.text,
        box=box,
        page=_page(path),
        location=error.location,
    )


def _form_path(location: str) -> str | None:
    """Turn HMRC's ``/hd:GovTalkMessage[1]/.../ct:TaxRate[1]`` into ``/IRenvelope/.../TaxRate``."""
    plain = _HMRC_LOCATION_NOISE.sub("", location)
    start = plain.find("/IRenvelope/")
    return plain[start:] if start >= 0 else None


def _page(path: str | None) -> PageCode | None:
    if path is None or not path.startswith(f"{RETURN_PATH}/"):
        return None
    element = path.removeprefix(f"{RETURN_PATH}/").split("/")[0].split("[")[0]
    return _PAGE_BY_ELEMENT.get(element)


def _invalid(problems: list[Problem]) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "error": "invalid_return",
            "message": "HMRC would reject this return. Fix the problems listed and try again.",
            "correlation_id": None,
            "errors": [_located(problem).model_dump() for problem in problems],
        },
    )


def _hmrc_failure(error: TransactionEngineError) -> HTTPException:
    code, name = next((code, name) for kind, code, name in _FAILURES if isinstance(error, kind))
    return _failure(
        code,
        name,
        str(error),
        correlation_id=error.correlation_id or None,
        errors=[_hmrc_error(each).model_dump() for each in error.errors],
    )


def _failure(
    code: int,
    error: str,
    message: str,
    *,
    correlation_id: str | None = None,
    errors: list[dict[str, object]] | None = None,
) -> HTTPException:
    detail = {"error": error, "message": message, "correlation_id": correlation_id}
    return HTTPException(code, detail={**detail, "errors": errors or []})
