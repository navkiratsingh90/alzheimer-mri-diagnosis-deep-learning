from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.prediction import Prediction
from app.ml.ml_loader import predict_image

router = APIRouter(tags=["upload"])

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file(file: UploadFile):
    """Check file extension and size."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    # Size check – we have to read the file to know size, but we can check after saving.
    # We'll save first and then check.

@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid file or prediction error"},
        401: {"description": "Unauthorized"},
    },
)
async def upload_mri(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload an MRI image, classify it, and save the result.

    - **file**: image file (JPG, PNG, BMP, TIFF) up to 10 MB.
    Returns the prediction result and confidence.
    """
    # Validate extension
    validate_file(file)

    # Create upload directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate a safe filename with timestamp to avoid collisions
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    file_path = file_path.replace("\\", "/")  # ← add this line 
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Check file size after saving
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(file_path)  # clean up
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    # Run prediction
    try:
        result, confidence = predict_image(file_path)
    except Exception as e:
        # Clean up saved file if prediction fails
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

    # Save prediction to database
    prediction = Prediction(
        user_id=user.id,
        image_path=file_path,   # relative path from project root
        result=result,
        confidence=confidence,
        timestamp=datetime.utcnow()
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    # Return response
    return {
        "id": prediction.id,
        "image_path": file_path,
        "result": result,
        "confidence": confidence,
        "timestamp": prediction.timestamp.isoformat(),
        "message": "Prediction saved successfully"
    }