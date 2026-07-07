from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, UserRole
from app.models.prediction import Prediction
from app.schemas.admin import UserAdminResponse, UpdateRoleRequest
from app.schemas.prediction import PredictionResponse

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── User Management ────────────────────────────────────────────

@router.get(
    "/users",
    response_model=List[UserAdminResponse],
    responses={
        403: {"description": "Admin access required"},
    },
)
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all registered users with their roles.
    """
    users = db.query(User).all()
    return users


@router.patch(
    "/users/{user_id}/role",
    response_model=dict,
    responses={
        400: {"description": "Invalid role or self-modification"},
        404: {"description": "User not found"},
        403: {"description": "Admin access required"},
    },
)
async def update_user_role(
    user_id: int,
    req: UpdateRoleRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update the role of a user (promote/demote).
    Cannot change your own role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role."
        )

    user.role = req.role
    db.commit()
    return {"message": f"User {user.username} role updated to {req.role.value}"}


@router.delete(
    "/users/{user_id}",
    response_model=dict,
    responses={
        400: {"description": "Cannot delete yourself"},
        404: {"description": "User not found"},
        403: {"description": "Admin access required"},
    },
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a user. Cannot delete yourself.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account."
        )

    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}


# ─── Prediction Management ──────────────────────────────────────

@router.get(
    "/predictions",
    response_model=List[PredictionResponse],
    responses={
        403: {"description": "Admin access required"},
    },
)
async def list_all_predictions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get all predictions from all users, newest first.
    """
    predictions = db.query(Prediction).order_by(Prediction.timestamp.desc()).all()
    return predictions


@router.delete(
    "/predictions/{prediction_id}",
    response_model=dict,
    responses={
        404: {"description": "Prediction not found"},
        403: {"description": "Admin access required"},
    },
)
async def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a specific prediction by ID.
    """
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    db.delete(pred)
    db.commit()
    return {"message": f"Prediction {prediction_id} deleted successfully"}