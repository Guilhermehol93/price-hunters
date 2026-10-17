"""Authentication dependencies for administrative API operations."""

import hmac

from fastapi import Header, HTTPException

from app.config import settings


def require_api_access(authorization: str | None = Header(default=None)) -> None:
    """Require the configured shared API token for privileged operations when configured."""
    expected = settings.API_ACCESS_TOKEN
    if not expected:
        return

    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Autenticação necessária.", headers={"WWW-Authenticate": "Bearer"})
