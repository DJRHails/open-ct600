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
    MAX_PASSWORD_LENGTH,
    MAX_USER_ID_LENGTH,
    Environment,
    GatewayCredentials,
    GovTalkError,
    Receipt,
    Vendor,
    build_submission,
)
from open_ct600.hmrc.irmark import IRmark
from open_ct600.hmrc.validate import Problem, validate_return
from open_ct600.hmrc.xml import build_return_xml
from open_ct600.hmrc.xmldoc import serialise
from open_ct600.ixbrl.accounts import render_accounts
from open_ct600.ixbrl.computations import render_computations
from open_ct600.ixbrl.layout import IxbrlRenderError
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
    gateway_user_id: Annotated[str, Field(min_length=1, max_length=MAX_USER_ID_LENGTH)]
    gateway_password: Annotated[SecretStr, Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)]


class SubmissionStatus(BaseModel):
    """Whether this deployment submits returns to HMRC.

    Attributes:
        enabled: Whether ``POST /api/returns/submit-to-hmrc`` is switched on. When it is not,
            do not ask for Government Gateway credentials at all.
        environments: Where a submission can go when enabled.
    """

    enabled: bool
    environments: list[Literal["test-in-live", "live"]]


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
        documents_attached: Whether the iXBRL accounts and computations could both be
            produced. A missing document is reported under HMRC's rule for it (9113 accounts,
            9965 computations) with the reason it is missing, such as no computations taxonomy
            for periods ending after 31 March 2026.
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


Document = Literal["accounts", "computations"]


@dataclass(frozen=True)
class IXBRLDocuments:
    """The iXBRL accounts and computations filed with a return.

    Attributes:
        accounts: The accounts XHTML, if they could be produced.
        computations: The computations XHTML, if they could be produced.
        missing: Why each document that could not be produced is missing, such as
            computations for a period HMRC has no computations taxonomy for yet.
    """

    accounts: str | None
    computations: str | None
    missing: dict[Document, str]


type IXBRLRenderer = Callable[[CT600Return, ReturnComputation], IXBRLDocuments]

_HMRC_CODES_FOR_MISSING: dict[Document, tuple[int, ...]] = {
    "accounts": (9113, 9315),
    "computations": (9965, 9316),
}
"""HMRC's rules that fire when a document is missing from the return."""


def render_ixbrl(ct600: CT600Return, computation: ReturnComputation) -> IXBRLDocuments:
    """Render the return's iXBRL accounts and computations, noting any that cannot be."""
    missing: dict[Document, str] = {}
    documents: dict[Document, str | None] = {}
    renderers: dict[Document, Callable[[CT600Return, ReturnComputation], str]] = {
        "accounts": render_accounts,
        "computations": render_computations,
    }
    for name, render in renderers.items():
        try:
            documents[name] = render(ct600, computation)
        except IxbrlRenderError as error:
            documents[name] = None
            missing[name] = str(error)
    return IXBRLDocuments(documents["accounts"], documents["computations"], missing)


def ixbrl_renderer() -> IXBRLRenderer:
    """Dependency: the function that renders a return's iXBRL documents."""
    return render_ixbrl


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
    router = APIRouter(prefix="/api", tags=["hmrc"])
    router.add_api_route("/returns/validate", check_return, methods=["POST"])
    router.add_api_route(
        "/returns/ct600.xml", download_xml, methods=["POST"], response_class=Response
    )

    def submission_status() -> SubmissionStatus:
        """Say whether this deployment submits to HMRC (ask for credentials only if so)."""
        return SubmissionStatus(
            enabled=_submission_enabled(settings), environments=["test-in-live", "live"]
        )

    async def submit_to_hmrc(
        request: SubmitRequest,
        http: Annotated[httpx2.AsyncClient, Depends(http_client)],
        render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)],
    ) -> HMRCReceipt | HMRCRejection:
        """Submit a declared return to HMRC and return HMRC's answer."""
        return await _submit(settings, request, http, render)

    router.add_api_route("/submission", submission_status, methods=["GET"])
    router.add_api_route("/returns/submit-to-hmrc", submit_to_hmrc, methods=["POST"])
    return router


def check_return(
    request: ReturnRequest, render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)]
) -> ValidationReport:
    """Check a return against HMRC's CT600 schema and business rules, offline."""
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    envelope = _envelope(request.ct600, computation, _declaration(request), documents)
    reasons = {
        code: reason
        for name, reason in documents.missing.items()
        for code in _HMRC_CODES_FOR_MISSING[name]
    }
    problems = [
        _located(problem, message=reasons.get(problem.code))
        for problem in validate_return(envelope)
    ]
    return ValidationReport(
        valid=not problems, documents_attached=not documents.missing, problems=problems
    )


def download_xml(
    request: ReturnRequest, render: Annotated[IXBRLRenderer, Depends(ixbrl_renderer)]
) -> Response:
    """Download the return's CT600 XML (the ``IRenvelope`` with the iXBRL it can attach).

    A document that cannot be produced is left out, and the response says so in
    ``X-CT600-Missing-Attachments`` (``accounts``, ``computations``) and
    ``X-CT600-Missing-Reason``.
    """
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    envelope = _envelope(request.ct600, computation, _declaration(request), documents)
    company, period = request.ct600.company, request.ct600.period
    filename = f"ct600-{company.utr}-{period.end.isoformat()}.xml"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if documents.missing:
        headers["X-CT600-Missing-Attachments"] = ", ".join(documents.missing)
        reasons = "; ".join(documents.missing.values())
        headers["X-CT600-Missing-Reason"] = reasons.encode("ascii", "replace").decode("ascii")
    return Response(content=serialise(envelope), media_type="application/xml", headers=headers)


async def _submit(
    settings: Settings,
    request: SubmitRequest,
    http: httpx2.AsyncClient,
    render: IXBRLRenderer,
) -> HMRCReceipt | HMRCRejection:
    vendor = _vendor(settings)
    environment = Environment(request.environment)
    # Computing, rendering, validating and IRmarking take up to a few hundred milliseconds;
    # a worker thread keeps them off the event loop that other submissions' polls run on.
    message, irmark = await run_in_threadpool(_prepare, request, render, environment, vendor)
    client = TransactionEngineClient(environment, http=http, max_wait=POLL_TIMEOUT_SECONDS)
    failure: HTTPException | None = None
    try:
        outcome = await client.submit(message)
    except TransactionEngineError as error:
        failure = _hmrc_failure(error)
    if failure is not None:
        # Raised outside the except block, so HMRC's error is not attached as its context.
        raise failure
    if isinstance(outcome, BusinessErrors):
        return HMRCRejection(
            environment=environment,
            correlation_id=outcome.correlation_id,
            errors=[_hmrc_error(error) for error in outcome.errors],
        )
    return _receipt(outcome, environment, irmark.base32)


def _prepare(
    request: SubmitRequest, render: IXBRLRenderer, environment: Environment, vendor: Vendor
) -> tuple[bytes, IRmark]:
    """Build the IRmarked GovTalk message, refusing a return HMRC would not accept."""
    computation = compute_return(request.ct600)
    documents = render(request.ct600, computation)
    if documents.missing:
        raise _failure(
            status.HTTP_409_CONFLICT,
            "ixbrl_unavailable",
            "HMRC needs the company's accounts and tax computations in iXBRL with the return, "
            f"so it cannot be submitted: {'; '.join(documents.missing.values())}.",
        )
    envelope = _envelope(request.ct600, computation, request.declaration, documents)
    problems = validate_return(envelope)
    if problems:
        raise _invalid(problems)
    credentials = GatewayCredentials(
        user_id=request.gateway_user_id, password=request.gateway_password
    )
    return build_submission(
        envelope, environment=environment, vendor=vendor, credentials=credentials
    )


def _submission_enabled(settings: Settings) -> bool:
    return settings.hmrc_submission_enabled and settings.hmrc_vendor_id is not None


def _vendor(settings: Settings) -> Vendor:
    if not _submission_enabled(settings) or settings.hmrc_vendor_id is None:
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
    documents: IXBRLDocuments,
) -> etree._Element:
    return build_return_xml(
        ct600,
        computation,
        declaration=declaration,
        accounts_xhtml=documents.accounts,
        computations_xhtml=documents.computations,
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


def _located(problem: Problem, *, message: str | None = None) -> ReturnProblem:
    """Place a problem on the form, optionally explaining it better than HMRC's message."""
    return ReturnProblem(
        code=problem.code,
        message=message or problem.message,
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
