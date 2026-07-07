from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.pdf_ingestion import ingest_pdf
import os
import shutil

router = APIRouter(prefix="/pdf", tags=["pdf"])

UPLOAD_DIR = "static/uploads/pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save the file
    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest into vector store (async processing – can be offloaded to Celery)
    try:
        result = ingest_pdf(file_path, user.id)
        return {"message": result}
    except Exception as e:
        # Clean up file if ingestion fails
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")