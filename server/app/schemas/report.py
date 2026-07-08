from pydantic import BaseModel
from datetime import datetime

class ReportCreate(BaseModel):
    title: str | None = None
    summary: str | None = None
    # prediction_ids: str | None = None  # or list[int]



class ReportResponse(BaseModel):
    id: int
    user_id: int
    # prediction_ids: str   # or prediction_id if you changed
    title: str
    summary: str
    file_path: str
    created_at: datetime