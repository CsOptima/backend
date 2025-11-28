from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float
from src.core.db import Base


class HTMLCash(Base):
    __tablename__ = "html_cashes"

    code = Column(String, primary_key=True)
    position = Column(Float, nullable=False)
    word = Column(Float, nullable=False)
    citation = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
