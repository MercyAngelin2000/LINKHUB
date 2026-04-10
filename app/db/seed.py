"""
Seed script — creates 3 tenants with distinct themes + mock analytics data.
Run: python -m db.seed
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.tenant import Tenant
from app.models.link import Link, Click
from datetime import datetime, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Clear existing data ───────────────────────────────────────
db.query(Click).delete()
db.query(Link).delete()
db.query(Tenant).delete()
db.commit()

# ── 3 Tenants with DISTINCT themes ───────────────────────────
tenants_data = [
    {
        "name": "Alex Rivera",
        "subdomain": "alex",
        "password": "password123",
        "bio": "Designer & Creative Director 🎨",
        "avatar": "🎨",
        "theme_config": {
            "preset": "midnight",
            "primary": "#a855f7",
            "background": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
            "text": "#f1f5f9",
            "radius": "999px",
            "font": "Space Grotesk",
            "buttonStyle": "gradient",
            "buttonGradient": "linear-gradient(135deg, #a855f7, #6366f1)",
        },
        "links": [
            {"title": "My Portfolio", "url": "https://alexrivera.design", "icon": "🎨"},
            {"title": "Dribbble", "url": "https://dribbble.com", "icon": "🏀"},
            {"title": "Instagram", "url": "https://instagram.com", "icon": "📸"},
            {"title": "Behance", "url": "https://behance.net", "icon": "✨"},
            {"title": "Buy me a coffee", "url": "https://buymeacoffee.com", "icon": "☕"},
        ]
    },
    {
        "name": "Sarah Chen",
        "subdomain": "sarah",
        "password": "password123",
        "bio": "Full-stack developer & open source contributor",
        "avatar": "💻",
        "theme_config": {
            "preset": "minimal",
            "primary": "#10b981",
            "background": "#ffffff",
            "text": "#111827",
            "radius": "8px",
            "font": "DM Mono",
            "buttonStyle": "outline",
            "buttonBorder": "2px solid #111827",
        },
        "links": [
            {"title": "GitHub", "url": "https://github.com", "icon": "🐙"},
            {"title": "Tech Blog", "url": "https://dev.to", "icon": "📝"},
            {"title": "LinkedIn", "url": "https://linkedin.com", "icon": "💼"},
            {"title": "YouTube Tutorials", "url": "https://youtube.com", "icon": "▶️"},
            {"title": "Newsletter", "url": "https://substack.com", "icon": "📧"},
        ]
    },
    {
        "name": "Marcus Beats",
        "subdomain": "marcus",
        "password": "password123",
        "bio": "Music producer & DJ 🎵 Booking open",
        "avatar": "🎵",
        "theme_config": {
            "preset": "neon",
            "primary": "#f59e0b",
            "background": "linear-gradient(180deg, #000000 0%, #1a0a00 100%)",
            "text": "#fef3c7",
            "radius": "4px",
            "font": "Bebas Neue",
            "buttonStyle": "neon",
            "glowColor": "#f59e0b",
        },
        "links": [
            {"title": "Spotify", "url": "https://spotify.com", "icon": "🎵"},
            {"title": "SoundCloud", "url": "https://soundcloud.com", "icon": "🔊"},
            {"title": "Book a Show", "url": "https://calendly.com", "icon": "📅"},
            {"title": "Merch Store", "url": "https://shopify.com", "icon": "👕"},
            {"title": "TikTok", "url": "https://tiktok.com", "icon": "🎬"},
        ]
    }
]

sources = ["direct", "instagram", "twitter", "tiktok", "other"]

for t_data in tenants_data:
    tenant = Tenant(
        name=t_data["name"],
        subdomain=t_data["subdomain"],
        password=t_data["password"],
        bio=t_data["bio"],
        avatar=t_data["avatar"],
        theme_config=t_data["theme_config"],
    )
    db.add(tenant)
    db.flush()

    links = []
    for i, l in enumerate(t_data["links"]):
        link = Link(
            title=l["title"],
            url=l["url"],
            icon=l["icon"],
            order=i + 1,
            tenant_id=tenant.id
        )
        db.add(link)
        db.flush()
        links.append(link)

    # Generate mock click data — last 30 days
    for link in links:
        num_clicks = random.randint(20, 200)
        for _ in range(num_clicks):
            days_ago = random.randint(0, 30)
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,5,8,10,10,9,8,9,10,10,9,8,7,6,5,4,3,2],
                k=1
            )[0]
            ts = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0,23)) + timedelta(hours=hour)
            click = Click(
                link_id=link.id,
                source=random.choices(sources, weights=[40,25,15,10,10], k=1)[0],
                timestamp=ts
            )
            db.add(click)

db.commit()
print("✅ Seeded 3 tenants with themes, links, and mock analytics data")
print("   Subdomains: alex, sarah, marcus")
print("   Password: password123 (all)")
db.close()