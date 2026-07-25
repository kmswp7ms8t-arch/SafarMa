from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from auth import ClientIdentity, issue_or_validate_client

ACCESS_HEADER = "X-Belink-Access"
ACCESS_VERSION = "a1"
_EPHEMERAL_SECRET = secrets.token_bytes(32)


@dataclass(frozen=True)
class AccessGrant:
    client_id: str
    expires_at: int
    token: str


@dataclass(frozen=True)
class AIRequestContext:
    identity: ClientIdentity
    access: AccessGrant | None


def access_required() -> bool:
    return os.getenv("BELINK_REQUIRE_ACCESS", "false").casefold() == "true"


def has_pilot_code() -> bool:
    return bool(
        os.getenv("BELINK_PILOT_ACCESS_CODE", "").strip()
        or os.getenv("BELINK_PILOT_ACCESS_CODE_SHA256", "").strip()
    )


def _secret() -> bytes:
    configured = (
        os.getenv("BELINK_ACCESS_SECRET", "").strip()
        or os.getenv("BELINK_SESSION_SECRET", "").strip()
    )
    return configured.encode("utf-8") if configured else _EPHEMERAL_SECRET


def _signature(client_id: str, expires_at: int) -> str:
    payload = f"{ACCESS_VERSION}|{client_id}|{expires_at}".encode("ascii")
    digest = hmac.new(_secret(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_pilot_code(code: str) -> bool:
    candidate = (code or "").strip()
    if not candidate or len(candidate) > 128:
        return False

    expected_hash = os.getenv("BELINK_PILOT_ACCESS_CODE_SHA256", "").strip().casefold()
    if expected_hash:
        supplied_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        return hmac.compare_digest(supplied_hash, expected_hash)

    expected = os.getenv("BELINK_PILOT_ACCESS_CODE", "").strip()
    return bool(expected) and hmac.compare_digest(candidate, expected)


def issue_access_token(client_id: str, *, now: int | None = None) -> AccessGrant:
    issued_at = int(now if now is not None else time.time())
    ttl_days = max(1, min(int(os.getenv("BELINK_ACCESS_TTL_DAYS", "30")), 365))
    expires_at = issued_at + ttl_days * 86_400
    signature = _signature(client_id, expires_at)
    token = f"{ACCESS_VERSION}.{client_id}.{expires_at}.{signature}"
    return AccessGrant(client_id=client_id, expires_at=expires_at, token=token)


def validate_access_token(
    token: str | None,
    client_id: str | None = None,
    *,
    now: int | None = None,
) -> AccessGrant | None:
    value = (token or "").strip()
    parts = value.split(".")
    if len(parts) != 4 or parts[0] != ACCESS_VERSION:
        return None

    token_client_id, expires_text, supplied = parts[1], parts[2], parts[3]
    if client_id and token_client_id != client_id:
        return None
    try:
        expires_at = int(expires_text)
    except ValueError:
        return None
    current = int(now if now is not None else time.time())
    if expires_at <= current:
        return None
    expected = _signature(token_client_id, expires_at)
    if not hmac.compare_digest(supplied, expected):
        return None
    return AccessGrant(client_id=token_client_id, expires_at=expires_at, token=value)


def authorize_ai_request(request: Request) -> AIRequestContext:
    identity = issue_or_validate_client(request)

    # Offline analysis never spends OpenAI usage and remains available without a pilot code.
    if not os.getenv("OPENAI_API_KEY") or not access_required():
        return AIRequestContext(identity=identity, access=None)

    if not has_pilot_code():
        raise HTTPException(status_code=503, detail="Pilot access is not configured")

    grant = validate_access_token(request.headers.get(ACCESS_HEADER), identity.client_id)
    if grant is None:
        raise HTTPException(status_code=403, detail="Pilot access code required")
    return AIRequestContext(identity=identity, access=grant)
