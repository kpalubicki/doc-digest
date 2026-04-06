"""Optional API key authentication dependency."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(_api_key_header)) -> None:
    """Enforce API key auth when API_KEY is set in config. No-op otherwise."""
    if settings.api_key is None:
        return
    if not key or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
