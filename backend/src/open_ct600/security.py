"""HTTP hardening shared by every route: safe validation errors, a body size limit, headers.

The submission route receives a Government Gateway password, so nothing here may echo a
request back: FastAPI's default 422 includes each error's ``input`` (for a missing field, the
whole request, password included).
"""

import base64
import hashlib
import re

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
DOCS_PATHS = frozenset({"/docs", "/redoc"})
"""FastAPI's interactive API docs, which get ``docs_policy`` instead of the strict policy."""
_INLINE_SCRIPT = re.compile(
    r"""(?xs)
    <script>              # an inline script: no src attribute
    (?P<code> .*? )       # its exact text, which is what a CSP hash covers
    </script>
    """
)
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
    """Add ``SECURITY_HEADERS`` to every HTTP response (``docs_policy`` for the API docs)."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap ``app``."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Add the headers as the response starts."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope["path"] in DOCS_PATHS:
            await self.app(scope, receive, _DocsResponse(send))
            return

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = _with_security_headers(message, SECURITY_HEADERS)
            await send(message)

        await self.app(scope, receive, with_headers)


class _DocsResponse:
    """Hold back an API docs page until its body is known, then send it with ``docs_policy``."""

    def __init__(self, send: Send) -> None:
        self._send = send
        self._start: Message | None = None
        self._body = b""

    async def __call__(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self._start = message
            return
        if message["type"] != "http.response.body" or self._start is None:
            await self._send(message)
            return
        self._body += message.get("body", b"")
        if message.get("more_body", False):
            return
        policy = docs_policy(self._body.decode("utf-8", errors="replace"))
        headers = {**SECURITY_HEADERS, "Content-Security-Policy": policy}
        await self._send({**self._start, "headers": _with_security_headers(self._start, headers)})
        await self._send({"type": "http.response.body", "body": self._body})


def _with_security_headers(start: Message, security: dict[str, str]) -> list[tuple[bytes, bytes]]:
    headers = list(start.get("headers", []))
    present = {name.lower() for name, _ in headers}
    for name, value in security.items():
        if name.lower().encode() not in present:
            headers.append((name.lower().encode(), value.encode()))
    return headers


def docs_policy(html: str) -> str:
    """The Content-Security-Policy for FastAPI's ``/docs`` (Swagger UI) and ``/redoc`` pages.

    They load their scripts and styles from jsDelivr, Redoc its fonts from Google Fonts, and
    both a favicon from fastapi.tiangolo.com. Swagger UI's inline bootstrap script is allowed
    by hash, computed from the page being sent, so no other inline script can run. Styles
    need ``'unsafe-inline'``: Redoc injects ``<style>`` elements at run time, which no hash
    can name. Swagger UI draws its icons from ``data:`` images; Redoc runs its search in a
    ``blob:`` worker. Framing, plugins and foreign form targets stay forbidden as everywhere.
    """
    scripts = ["'self'", "https://cdn.jsdelivr.net", *_inline_script_hashes(html)]
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src {' '.join(scripts)}",
            "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com "
            "'unsafe-inline'",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly",
            "worker-src 'self' blob:",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


def _inline_script_hashes(html: str) -> list[str]:
    return [
        "'sha256-{}'".format(
            base64.b64encode(hashlib.sha256(match.group("code").encode()).digest()).decode()
        )
        for match in _INLINE_SCRIPT.finditer(html)
    ]
