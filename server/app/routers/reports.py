from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.prediction import Prediction
from app.models.report import Report
from app.schemas.prediction import PredictionResponse
from app.schemas.report import ReportCreate, ReportResponse
from app.services.pdf_generator import generate_pdf_report
from app.services.ai_summary import generate_ai_summary

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all predictions for the user, newest first."""
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.timestamp.desc())
        .all()
    )
    return predictions

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prediction_id = payload.get("prediction_id")
    if not prediction_id:
        raise HTTPException(400, "prediction_id is required")
    
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == user.id
    ).first()
    if not prediction:
        raise HTTPException(404, "Prediction not found")

    # Prepare data for AI summary
    pred_data = {
        "result": prediction.result,
        "confidence": prediction.confidence,
        "timestamp": prediction.timestamp,
        "image_path": prediction.image_path,
    }
    summary = generate_ai_summary([pred_data])
    if not summary:
        summary = f"Patient diagnosed with {prediction.result} (confidence {prediction.confidence:.1%})."

    # Generate PDF
    title = f"Report – {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{user.id}_{timestamp_str}.pdf"
    reports_dir = "static/reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, filename)

    generate_pdf_report(title, summary, pred_data, file_path)

    # ✅ Use prediction_ids (String) column
    db_report = Report(
        user_id=user.id,
        title=title,
        summary=summary,
        file_path=file_path,
        # no prediction_ids
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return {
        "message": "Report generated",
        "report_id": db_report.id,
        "file_path": file_path
    }

@router.get("/list", response_model=List[ReportResponse])
async def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all reports for the user, newest first."""
    reports = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return reports

@router.get("/download/{report_id}")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download the PDF file for a specific report."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user.id
    ).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if not os.path.exists(report.file_path):
        raise HTTPException(404, "PDF file missing")
    return FileResponse(
        report.file_path,
        filename=os.path.basename(report.file_path),
        media_type="application/pdf"
    )