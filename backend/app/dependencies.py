"""Shared dependencies: authentication, rate limiting, and configuration."""

import hmac
import logging
import os

from fastapi import Request, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# ---------------------------------------------------------------------------
# API-key authentication
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY") or None
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "").lower() == "true"
TRUSTED_PROXY = os.getenv("TRUSTED_PROXY", "").lower() == "true"

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> None:
    """Validate the API key.

    If ``DISABLE_AUTH=true`` is set, authentication is skipped (local dev only).
    Otherwise, ``API_KEY`` **must** be configured or the server returns 500.

    Accepts the key via the ``X-API-Key`` header **or** an
    ``Authorization: Bearer <key>`` header.
    """
    if DISABLE_AUTH:
        return

    if API_KEY is None:
        raise StarletteHTTPException(
            status_code=500,
            detail="Server misconfiguration: API_KEY is not set. "
            "Set API_KEY or set DISABLE_AUTH=true for local development.",
        )

    # Try X-API-Key header first, then Authorization Bearer
    key = api_key
    if not key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            key = auth_header[len("Bearer "):]

    if not key or not hmac.compare_digest(key, API_KEY):
        raise StarletteHTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def _get_real_ip(request: Request) -> str:
    """Extract client IP, preferring X-Forwarded-For behind a trusted proxy."""
    if TRUSTED_PROXY:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first (leftmost) IP which is the original client
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip)


def log_startup_warnings() -> None:
    """Log warnings for missing configuration at startup."""
    if DISABLE_AUTH:
        logger.warning(
            "DISABLE_AUTH is set – authentication is disabled. "
            "Do NOT use this in production."
        )
    elif API_KEY is None:
        logger.warning(
            "API_KEY environment variable is not set and DISABLE_AUTH is not enabled. "
            "All requests will receive a 500 error until API_KEY is configured."
        )
