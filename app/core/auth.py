from typing import Optional

from fastapi import Header

from app.core.config import settings
from app.core.errors import UnauthorizedError


def require_api_key(x_statelock_api_key: Optional[str] = Header(default=None)) -> None:
    if not settings.AUTH_REQUIRED:
        return

    expected = settings.STATELOCK_API_KEY.strip()
    if not expected:
        raise UnauthorizedError("AUTH_REQUIRED is true but STATELOCK_API_KEY is not configured")

    if not x_statelock_api_key or x_statelock_api_key.strip() != expected:
        raise UnauthorizedError("Missing or invalid X-Statelock-Api-Key")
