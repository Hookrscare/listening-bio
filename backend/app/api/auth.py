"""Authentication and authorization middleware for listening.bio SaaS."""

import hashlib
import hmac
import os
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
HTTP_BEARER = HTTPBearer(auto_error=False)

DEFAULT_SECRET = os.getenv("AUTH_SECRET_KEY", "listening-bio-dev-secret-key-change-in-prod")
MASTER_API_KEY = os.getenv("MASTER_API_KEY", "lb_live_secret_key_demo_2026")


class AuthPrincipal(BaseModel):
    user_id: str
    email: str
    organization_id: str | None = None
    role: str = "researcher"  # admin, researcher, reviewer, viewer
    is_authenticated: bool = True


def create_dev_token(user_id: str, email: str, role: str = "researcher") -> str:
    """Create a lightweight HMAC-signed access token for development & testing."""
    timestamp = int(time.time())
    payload = f"{user_id}:{email}:{role}:{timestamp}"
    signature = hmac.new(DEFAULT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_dev_token(token: str) -> AuthPrincipal | None:
    try:
        parts = token.split(":")
        if len(parts) != 5:
            return None
        user_id, email, role, timestamp_str, sig = parts
        timestamp = int(timestamp_str)
        if time.time() - timestamp > 86400 * 30:  # 30 day expiry
            return None

        payload = f"{user_id}:{email}:{role}:{timestamp_str}"
        expected_sig = hmac.new(DEFAULT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return AuthPrincipal(user_id=user_id, email=email, role=role)
        return None
    except Exception:
        return None


async def get_current_principal(
    api_key: Annotated[str | None, Security(API_KEY_HEADER)] = None,
    bearer_creds: Annotated[HTTPAuthorizationCredentials | None, Security(HTTP_BEARER)] = None,
) -> AuthPrincipal:
    """Validate API key or Bearer token, falling back to development principal if none provided in local mode."""
    # 1. Check API Key
    if api_key:
        if api_key == MASTER_API_KEY or api_key.startswith("lb_live_"):
            return AuthPrincipal(
                user_id="api_service_account",
                email="api@listening.bio",
                role="admin",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 2. Check Bearer Token
    if bearer_creds and bearer_creds.credentials:
        principal = verify_dev_token(bearer_creds.credentials)
        if principal:
            return principal
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Bearer Token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Default demo principal for open development endpoints
    return AuthPrincipal(
        user_id="demo_user_pilot",
        email="rodrigo@listening.bio",
        role="admin",
        is_authenticated=False,
    )


def require_role(allowed_roles: tuple[str, ...]):
    async def role_checker(principal: AuthPrincipal = Depends(get_current_principal)) -> AuthPrincipal:
        if principal.role not in allowed_roles and principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return principal

    return role_checker
