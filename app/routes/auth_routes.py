from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from app.core.auth import create_access_token
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    subdomain: str
    password: str


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Tenant login. Returns a JWT scoped to this tenant.
    In production, use hashed passwords (bcrypt).
    """
    tenant = db.query(Tenant).filter(
        Tenant.subdomain == data.subdomain,
        Tenant.password == data.password  # use bcrypt in production
    ).first()

    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(tenant_id=tenant.id, subdomain=tenant.subdomain)

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "theme_config": tenant.theme_config,
        }
    }


@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    """Public profile endpoint — no auth needed, scoped by subdomain query param."""
    pass  # handled in links.py public route