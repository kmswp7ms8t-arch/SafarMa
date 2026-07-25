from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, Request

CLIENT_HEADER = "X-Belink-Client"
TOKEN_VERSION = "b1"
_CLIENT_RE = re.compile(r"^[a-f0-9]{32}$")
_EPHEMERAL_SECRET = secrets.token_bytes(32)


@dataclass(frozen=True)
class ClientIdentity:
    client_id: str
    token: str
    newly_issued: bool = False


def has_persistent_session_secret() -> bool:
    return bool(os.getenv("BELINK_SESSION_SECRET", "").strip())


def _secret() -> bytes:
    configured = os.getenv("BELINK_SESSION_SECRET", "").strip()
    return configured.encode("utf-8") if configured else _EPHEMERAL_SECRET


def _signature(client_id: str) -> str:
    digest = hmac.new(_secret(), client_id.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def issue_client_token(client_id: str | None = None) -> ClientIdentity:
    identifier = client_id or uuid.uuid4().hex
    if not _CLIENT_RE.fullmatch(identifier):
        raise ValueError("Invalid client identifier")
    return ClientIdentity(client_id=identifier, token=f"{TOKEN_VERSION}.{identifier}.{_signature(identifier)}", newly_issued=True)


def validate_client_token(token: str | None) -> ClientIdentity | None:
    value = (token or "").strip()
    parts = value.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_VERSION:
        return None
    client_id, supplied = parts[1], parts[2]
    if not _CLIENT_RE.fullmatch(client_id):
        return None
    expected = _signature(client_id)
    if not hmac.compare_digest(supplied, expected):
        return None
    return ClientIdentity(client_id=client_id, token=value, newly_issued=False)


def issue_or_validate_client(request: Request) -> ClientIdentity:
    raw = request.headers.get(CLIENT_HEADER)
    if not raw:
        return issue_client_token()
    identity = validate_client_token(raw)
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid Belink client token")
    return identity


def require_client(request: Request) -> ClientIdentity:
    identity = validate_client_token(request.headers.get(CLIENT_HEADER))
    if identity is None:
        raise HTTPException(status_code=401, detail="A valid Belink client token is required")
    return identity
