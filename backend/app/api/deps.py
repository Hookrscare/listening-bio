import hashlib
import hmac

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.config import Settings, get_settings
from backend.app.models import APIKey, Organization
from backend.app.models.entities import utc_now


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin_key(
    admin_key: str | None = Security(admin_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Protect mutable legacy routes when an admin key is configured."""
    if settings.admin_api_key is None:
        return
    if admin_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Admin-Key header.")
    if not hmac.compare_digest(admin_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key.")


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def get_current_organization(
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> Organization:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header.")

    candidate_hash = hash_api_key(api_key)
    key_record = db.scalar(select(APIKey).where(APIKey.key_hash == candidate_hash, APIKey.is_active.is_(True)))
    if key_record is None or not hmac.compare_digest(key_record.key_hash, candidate_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or revoked API key.")

    organization = db.get(Organization, key_record.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key organization is unavailable.")

    key_record.last_used_at = utc_now()
    db.flush()
    return organization
