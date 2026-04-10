from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()


def create_access_token(tenant_id: int, subdomain: str) -> str:
    """Create JWT token with tenant claims."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(tenant_id),
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Tenant:
    """
    Extract and validate tenant from JWT.
    This prevents cross-tenant access — token must match the tenant being accessed.
    """
    payload = decode_token(credentials.credentials)
    tenant_id = payload.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant claim in token")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


def verify_tenant_owns_link(link_id: int, tenant: Tenant, db: Session):
    """
    IDOR protection: verify the link belongs to the authenticated tenant.
    Prevents tenant A from accessing/modifying tenant B's links by guessing IDs.
    """
    from app.models.link import Link

    link = db.query(Link).filter(
        Link.id == link_id,
        Link.tenant_id == tenant.id   # ← scoped to tenant
    ).first()

    if not link:
        raise HTTPException(
            status_code=403,
            detail="Access denied: this resource does not belong to your tenant"
        )
    return link