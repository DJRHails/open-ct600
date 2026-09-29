"""Transaction Engine client: submit a CT600, poll for HMRC's answer, then delete it.

The submission message carries the Government Gateway password, so nothing here logs it, keeps
it, or lets it reach an exception: errors carry HMRC's error texts and the CorrelationID only,
and transport errors are re-raised without the request attached.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx2

from open_ct600.hmrc.govtalk import (
    SERVICES,
    Acknowledgement,
    DeleteConfirmation,
    Environment,
    ErrorReport,
    GovTalkError,
    Receipt,
    Reply,
    UnexpectedReplyError,
    build_delete,
    build_poll,
    parse_reply,
)
from open_ct600.hmrc.xmldoc import MalformedXMLError

logger = logging.getLogger(__name__)

_BUSINESS_ERRORS = 3001
_CORRELATION_ID_NOT_FOUND = 2000
_HTTP_FORBIDDEN = 403
_EDGE_REFUSAL_RETRY_DELAYS = (2.0, 5.0, 10.0)
"""Seconds to wait before each resend after Akamai's HTML 403."""


class TransactionEngineError(Exception):
    """HMRC or the Transaction Engine did not accept a message.

    Attributes:
        correlation_id: The submission's Transaction Engine identifier, when it has one.
        errors: The errors HMRC reported.
    """

    def __init__(
        self, message: str, *, correlation_id: str = "", errors: tuple[GovTalkError, ...] = ()
    ) -> None:
        super().__init__(message)
        self.correlation_id = correlation_id
        self.errors = errors


class AuthenticationFailedError(TransactionEngineError):
    """The Government Gateway credentials were refused (1002, 1046, 1047)."""


class MessageRejectedError(TransactionEngineError):
    """The message broke the GovTalk protocol or schema (1001 and other gateway errors)."""


class SubmissionTooLargeError(TransactionEngineError):
    """The message exceeds HMRC's size limit (2001, 1614: 25 MB)."""


class IRmarkRejectedError(TransactionEngineError):
    """HMRC's IRmark differs from the message's, or it is missing (2021, 2022)."""


class ProcessingFailedError(TransactionEngineError):
    """HMRC could not process the submission; resubmit later (1000, 2005, 3000)."""


class PollTimeoutError(TransactionEngineError):
    """HMRC did not answer in time. The submission may still be accepted."""


class UnexpectedResponseError(TransactionEngineError):
    """The reply was not a GovTalk message this client understands."""


class TransactionEngineUnavailableError(TransactionEngineError):
    """HMRC could not be reached."""


_ERRORS_BY_CODE: tuple[tuple[type[TransactionEngineError], frozenset[int]], ...] = (
    (IRmarkRejectedError, frozenset({2021, 2022})),
    (SubmissionTooLargeError, frozenset({2001, 1614})),
    (AuthenticationFailedError, frozenset({1002, 1046, 1047})),
    (ProcessingFailedError, frozenset({1000, 2005, 3000})),
)
"""Checked in order, over the header errors and HMRC's itemised details together."""


@dataclass(frozen=True)
class BusinessErrors:
    """HMRC rejected the return's content (3001); the user can correct it and resubmit.

    Attributes:
        correlation_id: The submission's Transaction Engine identifier (empty from TPVS).
        errors: HMRC's itemised errors: schema (4xxx), rules (9xxx) and iXBRL checks.
    """

    correlation_id: str
    errors: tuple[GovTalkError, ...]


type Outcome = Receipt | BusinessErrors


class TransactionEngineClient:
    """Submits GovTalk messages to one HMRC environment and waits for the outcome."""

    def __init__(
        self,
        environment: Environment,
        *,
        http: httpx2.AsyncClient,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        max_wait: float = 600.0,
    ) -> None:
        """Create a client.

        Args:
            environment: Where messages go.
            http: The HTTP client to send them with.
            sleep: Waits between polls (injectable for tests).
            clock: Monotonic seconds (injectable for tests).
            max_wait: Longest to keep polling before giving up, in seconds.
        """
        self._environment = environment
        self._service = SERVICES[environment]
        self._http = http
        self._sleep = sleep
        self._clock = clock
        self._max_wait = max_wait

    async def submit(self, message: bytes) -> Outcome:
        """Submit a message and return HMRC's answer.

        On the Transaction Engine this is submit, poll until answered, then delete the answer
        from the Transaction Engine. TPVS answers synchronously.

        Args:
            message: A GovTalk submission request (see ``govtalk.build_submission``).

        Returns:
            HMRC's receipt, or its business errors when it rejected the return's content.

        Raises:
            TransactionEngineError: A subclass naming why HMRC did not process the return.
        """
        reply = await self._exchange(self._service.submission_url, message)
        if isinstance(reply, Acknowledgement):
            reply = await self._poll(reply)
        finished = isinstance(reply, Receipt | ErrorReport) and reply.correlation_id
        if finished and self._service.poll_url is not None:
            await self._delete(reply.correlation_id, reply.endpoint)
        return _outcome(reply)

    async def _poll(self, acknowledgement: Acknowledgement) -> Reply:
        deadline = self._clock() + self._max_wait
        reply: Reply = acknowledgement
        while isinstance(reply, Acknowledgement):
            correlation_id = reply.correlation_id
            if self._clock() + reply.poll_interval > deadline:
                raise PollTimeoutError(
                    f"HMRC has not answered within {self._max_wait:.0f} seconds. The return may "
                    f"still be accepted: its Transaction Engine CorrelationID is {correlation_id}. "
                    "Check for HMRC's confirmation before submitting it again.",
                    correlation_id=correlation_id,
                )
            await self._sleep(reply.poll_interval)
            url = reply.endpoint or self._service.poll_url or self._service.submission_url
            reply = await self._exchange(url, build_poll(correlation_id, self._environment))
        return reply

    async def _delete(self, correlation_id: str, url: str | None) -> None:
        """Remove HMRC's answer from the Transaction Engine, as the protocol requires.

        A failure here does not change the outcome, and the Transaction Engine deletes answers
        itself after 30-60 days, so it is logged rather than raised.
        """
        endpoint = url or self._service.submission_url
        try:
            reply = await self._exchange(endpoint, build_delete(correlation_id, self._environment))
        except TransactionEngineError as error:
            logger.warning("Could not delete submission %s: %s", correlation_id, error)
            return
        not_found = isinstance(reply, ErrorReport) and any(
            error.number == _CORRELATION_ID_NOT_FOUND for error in reply.errors
        )
        if not isinstance(reply, DeleteConfirmation) and not not_found:
            logger.warning("Unexpected reply deleting submission %s: %r", correlation_id, reply)

    async def _exchange(self, url: str, content: bytes) -> Reply:
        response = await self._post(url, content)
        for delay in _EDGE_REFUSAL_RETRY_DELAYS:
            # TPVS sits behind Akamai, which intermittently refuses a request with an HTML 403
            # before it reaches HMRC (twice in a row has been seen), so it is safe to resend.
            if response.status_code != _HTTP_FORBIDDEN or not _is_html(response):
                break
            await self._sleep(delay)
            response = await self._post(url, content)
        if response.status_code != httpx2.codes.OK:
            raise UnexpectedResponseError(
                f"HMRC answered HTTP {response.status_code} "
                f"({response.headers.get('content-type', 'no content type')}) from {url}."
            )
        try:
            return parse_reply(response.content)
        except (MalformedXMLError, UnexpectedReplyError) as error:
            raise UnexpectedResponseError(
                f"HMRC's reply from {url} was not understood: {error}"
            ) from error

    async def _post(self, url: str, content: bytes) -> httpx2.Response:
        try:
            return await self._http.post(
                url, content=content, headers={"Content-Type": "application/xml"}
            )
        except httpx2.HTTPError as error:
            # Re-raised without chaining: the original holds the request, and its credentials.
            raise TransactionEngineUnavailableError(
                f"Could not reach HMRC at {url} ({type(error).__name__}: {error}). "
                "If this happened while submitting, the return may or may not have been sent."
            ) from None


def _is_html(response: httpx2.Response) -> bool:
    return response.headers.get("content-type", "").startswith("text/html")


def _outcome(reply: Reply) -> Outcome:
    """Turn HMRC's final reply into a receipt or business errors, raising for anything else."""
    if isinstance(reply, Receipt):
        return reply
    if not isinstance(reply, ErrorReport):
        raise UnexpectedResponseError(
            f"Expected HMRC's answer to a submission, got {type(reply).__name__}.",
            correlation_id=reply.correlation_id,
        )
    everything = reply.errors + reply.details
    numbers = {error.number for error in everything}
    for kind, codes in _ERRORS_BY_CODE:
        if numbers & codes:
            raise kind(
                _describe(everything), correlation_id=reply.correlation_id, errors=everything
            )
    if _BUSINESS_ERRORS in numbers:
        return BusinessErrors(reply.correlation_id, reply.details or reply.errors)
    raise MessageRejectedError(
        _describe(everything), correlation_id=reply.correlation_id, errors=everything
    )


def _describe(errors: tuple[GovTalkError, ...]) -> str:
    listed = "; ".join(f"{error.number}: {error.text}" for error in errors)
    return f"HMRC rejected the message: {listed or 'no error details given'}"
