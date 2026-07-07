from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)          # AI‑generated text summary
    file_path = Column(String(500), nullable=True) # Path to the saved PDF
    prediction_ids = Column(Text, nullable=True)   # comma‑separated list
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="reports")