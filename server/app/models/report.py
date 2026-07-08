from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    title = Column(String)
    summary = Column(Text)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    # remove prediction_ids if you want
    