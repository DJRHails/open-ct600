"""GovTalk 2.0 messages for CT600 filing: submit, poll and delete requests, and their replies.

Message shapes follow HMRC's "Transaction Engine: Document Submission Protocol" v2.0 and the
"Corporation Tax Online Service Validation Rules" v1.17a.
"""

import copy
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from open_ct600.hmrc.irmark import IRmark, add_irmark
from open_ct600.hmrc.xmldoc import (
    CT_NS,
    ERROR_RESPONSE_NS,
    GOVTALK_NS,
    SUCCESS_RESPONSE_NS,
    XMLDSIG_NS,
    parse_xml,
    serialise,
)

_CORRELATION_ID = re.compile(
    r"""(?x)
    [0-9A-F]{1,32}   # the Transaction Engine's upper-case hexadecimal submission identifier
    """
)
_VENDOR_ID = re.compile(
    r"""(?x)
    [0-9]{4}         # HMRC allocates each recognised software developer a 4-digit vendor ID
    """
)


class Environment(StrEnum):
    """Where a return is sent."""

    LIVE = "live"
    TEST_IN_LIVE = "test-in-live"
    ETS = "ets"
    TPVS = "tpvs"


@dataclass(frozen=True)
class Service:
    """How to reach one HMRC environment.

    Attributes:
        message_class: GovTalk ``Class`` for CT600 submissions.
        gateway_test: GovTalk ``GatewayTest`` flag (1 for HMRC's test services).
        submission_url: Where submissions are POSTed.
        poll_url: Where polls go when an acknowledgement names no ``ResponseEndPoint``;
            ``None`` for TPVS, which answers submissions synchronously.
        needs_credentials: Whether the Transaction Engine authenticates the sender.
    """

    message_class: str
    gateway_test: bool
    submission_url: str
    poll_url: str | None
    needs_credentials: bool


_LIVE_TE = "https://transaction-engine.tax.service.gov.uk"
_TEST_TE = "https://test-transaction-engine.tax.service.gov.uk"

SERVICES: dict[Environment, Service] = {
    Environment.LIVE: Service(
        "HMRC-CT-CT600", False, f"{_LIVE_TE}/submission", f"{_LIVE_TE}/poll", True
    ),
    Environment.TEST_IN_LIVE: Service(
        "HMRC-CT-CT600-TIL", False, f"{_LIVE_TE}/submission", f"{_LIVE_TE}/poll", True
    ),
    Environment.ETS: Service(
        "HMRC-CT-CT600", True, f"{_TEST_TE}/submission", f"{_TEST_TE}/poll", True
    ),
    Environment.TPVS: Service(
        "HMRC-CT-CT600", True, "https://www.tpvs.hmrc.gov.uk/HMRC/CT600", None, False
    ),
}


class GatewayCredentials(BaseModel):
    """A Government Gateway user ID and password. The password never appears in reprs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str = Field(min_length=1, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=256)


@dataclass(frozen=True)
class Vendor:
    """The software identifying itself in ``ChannelRouting``.

    Attributes:
        vendor_id: HMRC's 4-digit vendor ID for the software developer.
        product: Product name.
        version: Product version.
    """

    vendor_id: str
    product: str
    version: str

    def __post_init__(self) -> None:
        """Reject a vendor ID HMRC could not have issued."""
        if not _VENDOR_ID.fullmatch(self.vendor_id):
            raise ValueError(f"HMRC vendor IDs are 4 digits, got {self.vendor_id!r}.")


class MessageBuildError(ValueError):
    """A GovTalk message that cannot be built from the inputs given."""


def build_submission(
    ir_envelope: etree._Element,
    *,
    environment: Environment,
    vendor: Vendor,
    credentials: GatewayCredentials | None,
) -> tuple[bytes, IRmark]:
    """Wrap a CT600 ``IRenvelope`` in a GovTalk submission request and IRmark it.

    The envelope is copied without XML comments, and nothing is pretty-printed, so the IRmark
    covers exactly the data in the return.

    Args:
        ir_envelope: The return; its ``IRheader`` must hold a UTR key and an ``IRmark``
            placeholder.
        environment: Where the message is going.
        vendor: The submitting software.
        credentials: Government Gateway credentials; required except for TPVS, which must
            never be sent any.

    Returns:
        The serialised message and its IRmark.

    Raises:
        MessageBuildError: If the credentials do not suit the environment or the return has
            no UTR key.
    """
    service = SERVICES[environment]
    if service.needs_credentials and credentials is None:
        raise MessageBuildError(f"{environment} submissions need Government Gateway credentials.")
    if not service.needs_credentials and credentials is not None:
        raise MessageBuildError(f"{environment} takes no credentials; do not send them.")
    root, header = _message(service, qualifier="request", function="submit", correlation_id="")
    if credentials is not None:
        _sender_details(header, credentials)
    details = _sub(root, "GovTalkDetails")
    _sub(_sub(details, "Keys"), "Key", _utr(ir_envelope), Type="UTR")
    _sub(_sub(details, "TargetDetails"), "Organisation", "HMRC")
    channel = _sub(_sub(details, "ChannelRouting"), "Channel")
    _sub(channel, "URI", vendor.vendor_id)
    _sub(channel, "Product", vendor.product)
    _sub(channel, "Version", vendor.version)
    body = copy.deepcopy(ir_envelope)
    etree.strip_tags(body, etree.Comment)
    _sub(root, "Body").append(body)
    return add_irmark(serialise(root))


def build_poll(correlation_id: str, environment: Environment) -> bytes:
    """Build a SUBMISSION_POLL asking for the outcome of a submission."""
    return _follow_up(correlation_id, environment, qualifier="poll", function="submit")


def build_delete(correlation_id: str, environment: Environment) -> bytes:
    """Build a DELETE_REQUEST removing a finished submission from the Transaction Engine."""
    return _follow_up(correlation_id, environment, qualifier="request", function="delete")


def _follow_up(
    correlation_id: str, environment: Environment, *, qualifier: str, function: str
) -> bytes:
    if not _CORRELATION_ID.fullmatch(correlation_id):
        raise MessageBuildError(
            f"CorrelationID must be 1-32 upper-case hex digits, got {correlation_id!r}."
        )
    service = SERVICES[environment]
    root, _ = _message(
        service, qualifier=qualifier, function=function, correlation_id=correlation_id
    )
    _sub(_sub(root, "GovTalkDetails"), "Keys")
    return serialise(root)


def _message(
    service: Service, *, qualifier: str, function: str, correlation_id: str
) -> tuple[etree._Element, etree._Element]:
    root = etree.Element(f"{{{GOVTALK_NS}}}GovTalkMessage", nsmap={None: GOVTALK_NS})
    _sub(root, "EnvelopeVersion", "2.0")
    header = _sub(root, "Header")
    details = _sub(header, "MessageDetails")
    _sub(details, "Class", service.message_class)
    _sub(details, "Qualifier", qualifier)
    _sub(details, "Function", function)
    _sub(details, "CorrelationID", correlation_id or None)
    _sub(details, "Transformation", "XML")
    _sub(details, "GatewayTest", "1" if service.gateway_test else "0")
    return root, header


def _sender_details(header: etree._Element, credentials: GatewayCredentials) -> None:
    identity = _sub(_sub(header, "SenderDetails"), "IDAuthentication")
    _sub(identity, "SenderID", credentials.user_id)
    authentication = _sub(identity, "Authentication")
    _sub(authentication, "Method", "clear")
    _sub(authentication, "Role", "principal")
    _sub(authentication, "Value", credentials.password.get_secret_value())


def _utr(ir_envelope: etree._Element) -> str:
    key = ir_envelope.find(f"{{{CT_NS}}}IRheader/{{{CT_NS}}}Keys/{{{CT_NS}}}Key[@Type='UTR']")
    if key is None or not key.text:
        raise MessageBuildError("The return's IRheader has no UTR key to address it by.")
    return key.text


def _sub(
    parent: etree._Element, name: str, text: str | None = None, **attributes: str
) -> etree._Element:
    element = etree.SubElement(parent, f"{{{GOVTALK_NS}}}{name}", attributes)
    element.text = text
    return element


@dataclass(frozen=True)
class GovTalkError:
    """One error reported by the Transaction Engine or HMRC.

    Attributes:
        raised_by: Who raised it (``Gateway``, ``ChRIS``, ``Department``...).
        number: HMRC's error code, such as 1046 or 9319.
        error_type: ``fatal``, ``business`` or, for iXBRL checks, the validator's rule name.
        text: HMRC's message.
        location: Where in the message the error is, when HMRC says.
    """

    raised_by: str
    number: int | None
    error_type: str
    text: str
    location: str


@dataclass(frozen=True)
class Acknowledgement:
    """The Transaction Engine has the submission and is waiting for HMRC.

    Attributes:
        correlation_id: Identifies the submission in polls.
        endpoint: Where to poll (``ResponseEndPoint``), if the Transaction Engine said.
        poll_interval: Seconds to wait before polling.
    """

    correlation_id: str
    endpoint: str | None
    poll_interval: int


@dataclass(frozen=True)
class Receipt:
    """HMRC accepted the return.

    Attributes:
        correlation_id: The submission's Transaction Engine identifier (empty from TPVS).
        endpoint: Where to send the delete request (``ResponseEndPoint``), if given.
        irmark: The IRmark HMRC computed (Base64 ``DigestValue`` of the signed receipt).
        accepted_time: When HMRC accepted the return, on HMRC's clock.
        messages: HMRC's receipt messages, including the one quoting the Base32 IRmark.
        response: The complete signed response, for the company's records.
    """

    correlation_id: str
    endpoint: str | None
    irmark: str | None
    accepted_time: datetime | None
    messages: tuple[str, ...]
    response: bytes


@dataclass(frozen=True)
class ErrorReport:
    """The Transaction Engine or HMRC rejected a message.

    Attributes:
        correlation_id: The submission's identifier, if it got one.
        endpoint: Where to send follow-up messages (``ResponseEndPoint``), if given.
        errors: The ``GovTalkErrors`` in the header (1046, 3001...).
        details: The errors in the body's ``ErrorResponse``: HMRC's itemised business errors.
    """

    correlation_id: str
    endpoint: str | None
    errors: tuple[GovTalkError, ...]
    details: tuple[GovTalkError, ...]


@dataclass(frozen=True)
class DeleteConfirmation:
    """The Transaction Engine deleted a finished submission."""

    correlation_id: str


type Reply = Acknowledgement | Receipt | ErrorReport | DeleteConfirmation


class UnexpectedReplyError(ValueError):
    """A reply that is not a GovTalk message this client understands."""


def parse_reply(content: bytes) -> Reply:
    """Read a Transaction Engine (or TPVS) reply.

    Args:
        content: The HTTP response body.

    Returns:
        The reply, by its ``Qualifier`` and ``Function``.

    Raises:
        UnexpectedReplyError: If the reply is not a GovTalk message, or is one this protocol
            does not send to clients.
    """
    root = parse_xml(content)
    if root.tag != f"{{{GOVTALK_NS}}}GovTalkMessage":
        raise UnexpectedReplyError(f"Expected a GovTalkMessage, got {root.tag!r}.")
    qualifier = _text(root, "Header/MessageDetails/Qualifier")
    function = _text(root, "Header/MessageDetails/Function")
    correlation_id = _text(root, "Header/MessageDetails/CorrelationID")
    endpoint = _text(root, "Header/MessageDetails/ResponseEndPoint") or None
    match (qualifier, function):
        case ("acknowledgement", "submit"):
            return _acknowledgement(root, correlation_id, endpoint)
        case ("response", "submit"):
            return _receipt(root, correlation_id, endpoint, content)
        case ("error", _):
            return ErrorReport(correlation_id, endpoint, _header_errors(root), _body_errors(root))
        case ("response", "delete"):
            return DeleteConfirmation(correlation_id)
        case _:
            raise UnexpectedReplyError(
                f"Unexpected GovTalk reply: Qualifier={qualifier!r}, Function={function!r}."
            )


def _acknowledgement(
    root: etree._Element, correlation_id: str, endpoint: str | None
) -> Acknowledgement:
    element = root.find(_path("Header/MessageDetails/ResponseEndPoint"))
    interval = "" if element is None else element.get("PollInterval", "")
    if not correlation_id or not interval.isdigit():
        raise UnexpectedReplyError(
            "An acknowledgement must carry a CorrelationID and a numeric PollInterval, got "
            f"CorrelationID={correlation_id!r}, PollInterval={interval!r}."
        )
    return Acknowledgement(correlation_id, endpoint, int(interval))


def _receipt(
    root: etree._Element, correlation_id: str, endpoint: str | None, content: bytes
) -> Receipt:
    success = root.find(f"{_path('Body')}/{{{SUCCESS_RESPONSE_NS}}}SuccessResponse")
    if success is None:
        raise UnexpectedReplyError("A submission response has no SuccessResponse in its Body.")
    digest = success.find(f".//{{{XMLDSIG_NS}}}DigestValue")
    accepted = success.findtext(f"{{{SUCCESS_RESPONSE_NS}}}AcceptedTime")
    messages = success.iterfind(f".//{{{SUCCESS_RESPONSE_NS}}}Message")
    return Receipt(
        correlation_id=correlation_id,
        endpoint=endpoint,
        irmark=digest.text.strip() if digest is not None and digest.text else None,
        accepted_time=datetime.fromisoformat(accepted) if accepted else None,
        messages=tuple((message.text or "").strip() for message in messages),
        response=content,
    )


def _header_errors(root: etree._Element) -> tuple[GovTalkError, ...]:
    return tuple(
        _error(element, GOVTALK_NS)
        for element in root.iterfind(_path("GovTalkDetails/GovTalkErrors/Error"))
    )


def _body_errors(root: etree._Element) -> tuple[GovTalkError, ...]:
    response = f"{_path('Body')}/{{{ERROR_RESPONSE_NS}}}ErrorResponse"
    return tuple(
        _error(element, ERROR_RESPONSE_NS)
        for element in root.iterfind(f"{response}/{{{ERROR_RESPONSE_NS}}}Error")
    )


def _error(element: etree._Element, namespace: str) -> GovTalkError:
    def text(name: str) -> str:
        return (element.findtext(f"{{{namespace}}}{name}") or "").strip()

    number = text("Number")
    return GovTalkError(
        raised_by=text("RaisedBy"),
        number=int(number) if number.lstrip("-").isdigit() else None,
        error_type=text("Type"),
        text=" ".join(
            (part.text or "").strip() for part in element.iterfind(f"{{{namespace}}}Text")
        ),
        location=text("Location"),
    )


def _path(relative: str) -> str:
    return "/".join(f"{{{GOVTALK_NS}}}{name}" for name in relative.split("/"))


def _text(root: etree._Element, relative: str) -> str:
    return (root.findtext(_path(relative)) or "").strip()
