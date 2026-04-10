from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.db.database import Base
from datetime import datetime

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    url = Column(String)
    icon = Column(String, default="🔗")
    order = Column(Integer, default=0)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))

class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("links.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default="direct")