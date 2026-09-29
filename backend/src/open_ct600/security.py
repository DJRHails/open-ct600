"""HTTP hardening shared by every route: safe validation errors, a body size limit, headers.

The submission route receives a Government Gateway password, so nothing here may echo a
request back: FastAPI's default 422 includes each error's ``input`` (for a missing field, the
whole request, password included).
"""

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_BYTES = 2 * 1024 * 1024
"""Largest request body accepted: a full return with every page is well under 1 MB."""

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; "
        "form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
_SAFE_CONTEXT_KEYS = frozenset({"box"})
"""Error context kept in 422s: the CT600 box of a page answer. Other context (a validator's
exception, a pattern, an expected value) can quote the input, so it is dropped."""


async def validation_error_response(_: Request, error: Exception) -> JSONResponse:
    """Answer a request that fails validation with where and why, never with what was sent.

    Each error keeps ``loc``, ``msg`` and ``type`` (what the frontend maps to its fields) and
    only the ``box`` from ``ctx``; ``input`` and ``url`` are dropped.
    """
    if not isinstance(error, RequestValidationError):
        raise TypeError(f"Expected a RequestValidationError, got {type(error).__name__}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": [_without_input(problem) for problem in error.errors()]},
    )


def _without_input(problem: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {key: problem[key] for key in ("loc", "msg", "type")}
    context = problem.get("ctx")
    if isinstance(context, dict):
        kept = {key: value for key, value in context.items() if key in _SAFE_CONTEXT_KEYS}
        if kept:
            safe["ctx"] = kept
    return jsonable_encoder(safe)


class BodySizeLimit:
    """Refuse request bodies over ``max_bytes`` with 413, by declared or streamed size."""

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        """Wrap ``app``."""
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Check the declared length, then count the body as the app reads it."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._too_large()(scope, receive, send)
            return
        received = 0

        async def limited() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, self._message())
            return message

        await self.app(scope, limited, send)

    def _message(self) -> str:
        return f"The request is too large: send no more than {self.max_bytes // 1024} KB."

    def _too_large(self) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, content={"detail": self._message()}
        )


class SecurityHeaders:
    """Add ``SECURITY_HEADERS`` to every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap ``app``."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Add the headers as the response starts."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name.lower().encode() not in present:
                        headers.append((name.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, with_headers)
