from sqlalchemy import Column, Integer, String, JSON
from app.db.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    subdomain = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)          # bcrypt hash in production
    bio = Column(String, nullable=True)
    avatar = Column(String, nullable=True)  # URL or emoji
    theme_config = Column(JSON, default={
        "primary": "#6366f1",
        "background": "#f8fafc",
        "text": "#1e293b",
        "radius": "12px",
        "font": "DM Sans",
        "preset": "default"
    })