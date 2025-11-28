from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float
from src.core.db import Base


class HTMLCash(Base):
    __tablename__ = "html_cashes"

    code = Column(String, primary_key=True)
    metric = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
