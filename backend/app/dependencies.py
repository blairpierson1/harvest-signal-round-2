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
_default_origins = "*" if os.getenv("FLY_APP_NAME") else "http://localhost:3000"
_origins_raw = os.getenv("ALLOWED_ORIGINS", _default_origins)
ALLOWED_ORIGINS = ["*"] if _origins_raw == "*" else _origins_raw.split(",")

# ---------------------------------------------------------------------------
# API-key authentication (optional – skipped when API_KEY is not set)
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY") or None

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> None:
    """Validate the API key if one is configured.

    Accepts the key via the ``X-API-Key`` header **or** an
    ``Authorization: Bearer <key>`` header.
    """
    if API_KEY is None:
        # No key configured – authentication disabled
        return

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
limiter = Limiter(key_func=get_remote_address)


def log_startup_warnings() -> None:
    """Log warnings for missing configuration at startup."""
    if API_KEY is None:
        logger.warning(
            "API_KEY environment variable is not set – authentication is disabled. "
            "Set API_KEY to enable API-key authentication."
        )
