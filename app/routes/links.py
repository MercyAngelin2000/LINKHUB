from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.link import Link, Click
from app.models.tenant import Tenant
from app.core.auth import get_current_tenant, verify_tenant_owns_link
from sqlalchemy import func
from fastapi import Body
from pydantic import BaseModel
from typing import List
import random
from datetime import datetime, timedelta

router = APIRouter()


# ─── PUBLIC ROUTE (no auth — for profile page viewers) ────────────────────────

@router.get("/public")
def get_public_links(tenant: str = Query(...), db: Session = Depends(get_db)):
    """
    Public profile page — readable by anyone with the subdomain.
    Does NOT expose private tenant data.
    """
    tenant_obj = db.query(Tenant).filter(Tenant.subdomain == tenant).first()

    if not tenant_obj:
        raise HTTPException(status_code=404, detail="Tenant not found")

    links = db.query(Link)\
        .filter(Link.tenant_id == tenant_obj.id)\
        .order_by(Link.order)\
        .all()

    return {
        "tenant_name": tenant_obj.name,
        "bio": tenant_obj.bio,
        "avatar": tenant_obj.avatar,
        "links": [{"id": l.id, "title": l.title, "url": l.url, "icon": l.icon} for l in links],
        "theme": tenant_obj.theme_config,
    }


# ─── PROTECTED ROUTES (require JWT with tenant claim) ──────────────────────────

@router.get("/")
def get_links(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get all links for the authenticated tenant (dashboard use)."""
    links = db.query(Link)\
        .filter(Link.tenant_id == tenant.id)\
        .order_by(Link.order)\
        .all()

    return {
        "links": links,
        "theme": tenant.theme_config,
        "tenant": {"name": tenant.name, "subdomain": tenant.subdomain}
    }


class LinkCreate(BaseModel):
    title: str
    url: str
    icon: str = "🔗"


@router.post("/")
def create_link(
    data: LinkCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new link for the authenticated tenant."""
    max_order = db.query(func.max(Link.order)).filter(Link.tenant_id == tenant.id).scalar() or 0

    link = Link(
        title=data.title,
        url=data.url,
        icon=data.icon,
        order=max_order + 1,
        tenant_id=tenant.id
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/{link_id}")
def delete_link(
    link_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete a link — IDOR protected.
    Tenant can only delete their own links even if they guess another ID.
    """
    link = verify_tenant_owns_link(link_id, tenant, db)
    db.delete(link)
    db.commit()
    return {"status": "deleted"}


class ReorderItem(BaseModel):
    id: int
    order: int


@router.post("/reorder")
def reorder_links(
    data: List[ReorderItem],
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Reorder links — validates all links belong to this tenant (IDOR protection)."""
    for item in data:
        link = db.query(Link).filter(
            Link.id == item.id,
            Link.tenant_id == tenant.id   # ← strict tenant scope
        ).first()

        if link:
            link.order = item.order

    db.commit()
    return {"status": "updated"}


@router.post("/click/{link_id}")
def track_click(
    link_id: int,
    request_source: str = Query(default="direct"),
    db: Session = Depends(get_db)
):
    """Track a click — public endpoint (no auth needed)."""
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    click = Click(link_id=link_id, source=request_source)
    db.add(click)
    db.commit()
    return {"status": "tracked"}


# ─── ANALYTICS (protected) ────────────────────────────────────────────────────

@router.get("/analytics/hourly")
def clicks_by_hour(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    data = db.query(
        func.extract('hour', Click.timestamp).label('hour'),
        func.count().label('count')
    ).join(Link).filter(
        Link.tenant_id == tenant.id
    ).group_by('hour').all()

    # Fill all 24 hours (even empty ones)
    counts = {int(d.hour): d.count for d in data}
    return [{"hour": h, "count": counts.get(h, 0)} for h in range(24)]


@router.get("/analytics/top-links")
def top_links(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    data = db.query(
        Link.title,
        func.count(Click.id).label("clicks")
    ).join(Click).filter(
        Link.tenant_id == tenant.id
    ).group_by(Link.title).order_by(func.count(Click.id).desc()).all()

    return [{"name": d.title, "clicks": d.clicks} for d in data]


@router.get("/analytics/sources")
def traffic_sources(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    data = db.query(
        Click.source,
        func.count().label("count")
    ).join(Link).filter(
        Link.tenant_id == tenant.id
    ).group_by(Click.source).all()

    # Fallback mock if no real data
    if not data:
        return [
            {"name": "Direct", "value": 60},
            {"name": "Instagram", "value": 25},
            {"name": "Twitter", "value": 10},
            {"name": "Other", "value": 5},
        ]

    return [{"name": d.source or "Direct", "value": d.count} for d in data]


@router.get("/analytics/summary")
def analytics_summary(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Summary stats for dashboard cards."""
    total_clicks = db.query(func.count(Click.id))\
        .join(Link).filter(Link.tenant_id == tenant.id).scalar() or 0

    total_links = db.query(func.count(Link.id))\
        .filter(Link.tenant_id == tenant.id).scalar() or 0

    # Clicks in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_clicks = db.query(func.count(Click.id))\
        .join(Link).filter(
            Link.tenant_id == tenant.id,
            Click.timestamp >= week_ago
        ).scalar() or 0

    return {
        "total_clicks": total_clicks,
        "total_links": total_links,
        "weekly_clicks": weekly_clicks,
    }


# ─── THEME UPDATE ──────────────────────────────────────────────────────────────

@router.put("/theme")
def update_theme(
    theme: dict = Body(...),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update tenant theme config."""
    tenant.theme_config = theme
    db.commit()
    return {"status": "updated", "theme": tenant.theme_config}