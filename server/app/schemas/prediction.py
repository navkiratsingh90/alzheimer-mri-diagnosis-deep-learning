from pydantic import BaseModel
from datetime import datetime

class PredictionResponse(BaseModel):
    id: int
    image_path: str | None
    result: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True