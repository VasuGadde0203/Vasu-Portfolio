"""Client identification, rate limiting and request-size protection."""

from __future__ import annotations

import hashlib
import logging
import random
import time

from fastapi import Depends, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings, get_settings
from app.db.repositories import RateLimitRepository
from app.db.session import get_session
from app.services.errors import ServiceError

log = logging.getLogger(__name__)


def client_key(request: Request, settings: Settings) -> str:
    ip = request.client.host if request.client else "unknown"
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        # The platform proxy appends the real client address last; earlier entries are spoofable.
        if forwarded:
            ip = forwarded.split(",")[-1].strip() or ip
    return hashlib.sha256(ip.encode()).hexdigest()[:32]


def enforce_contact_rate_limit(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> None:
    key = client_key(request, settings)
    window = int(time.time()) // 3600
    try:
        count = RateLimitRepository(session).hit(f"c:{key}", window)
    except SQLAlchemyError as exc:
        session.rollback()
        log.error("Rate limiter unavailable (%s)", type(exc).__name__)
        raise ServiceError("service_unavailable", "The service is temporarily unavailable.", 503) from exc
    if count > settings.contact_rate_limit_per_hour:
        raise ServiceError("rate_limited", "Too many messages sent. Please try again later or email me directly.", 429)


def enforce_rate_limit(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> None:
    """Counters live in PostgreSQL, so limits hold across multiple backend instances."""
    key = client_key(request, settings)
    now = int(time.time())
    repo = RateLimitRepository(session)
    try:
        minute = repo.hit(f"m:{key}", now // 60)
        day = repo.hit(f"d:{key}", now // 86400)
        if random.random() < 0.02:
            repo.purge_before(now // 86400 - 1)
    except SQLAlchemyError as exc:
        session.rollback()
        log.error("Rate limiter unavailable (%s)", type(exc).__name__)
        raise ServiceError("service_unavailable", "The service is temporarily unavailable.", 503) from exc
    if minute > settings.rate_limit_per_minute:
        raise ServiceError("rate_limited", "Too many questions in a short time. Please wait a minute.", 429)
    if day > settings.rate_limit_per_day:
        raise ServiceError("rate_limited", "Daily question limit reached. Please try again tomorrow.", 429)


class BodySizeLimitMiddleware:
    """Reject oversized bodies before they are parsed (checks Content-Length and streamed bytes)."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        declared = headers.get(b"content-length")
        if declared and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(send)
            return
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _TooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _TooLarge:
            await self._reject(send)

    @staticmethod
    async def _reject(send: Send) -> None:
        body = b'{"error":{"code":"payload_too_large","message":"Request is too large."}}'
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


class _TooLarge(Exception):
    pass


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers += [(b"x-content-type-options", b"nosniff"), (b"cache-control", b"no-store"),
                            (b"referrer-policy", b"no-referrer")]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
