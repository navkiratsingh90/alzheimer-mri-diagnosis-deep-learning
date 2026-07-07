from pydantic import BaseModel
from datetime import datetime

class ReportCreate(BaseModel):
    title: str | None = None
    summary: str | None = None
    prediction_ids: str | None = None  # or list[int]

class ReportResponse(BaseModel):
    id: int
    title: str | None
    summary: str | None
    prediction_ids: str | None
    created_at: datetime

    class Config:
        from_attributes = True