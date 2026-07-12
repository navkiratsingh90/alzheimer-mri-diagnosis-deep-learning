from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionResponse

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("", response_model=List[PredictionResponse])
async def get_predictions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve all predictions for the authenticated user, ordered newest first.
    """
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.timestamp.desc())
        .all()
    )
    return predictions