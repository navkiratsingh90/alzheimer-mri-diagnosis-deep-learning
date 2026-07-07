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
from server.app.services.pdf_generator import generate_pdf_report
from server.app.services.ai_summary import generate_ai_summary

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get(
    "/predictions",
    response_model=List[PredictionResponse],
    responses={401: {"description": "Unauthorized"}},
)
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

@router.post(
    "/generate",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
    },
)
async def generate_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Generate a PDF report with AI summary for the selected predictions.
    prediction_ids: comma‑separated list of prediction IDs.
    """
    # Parse prediction IDs
    ids = []
    if report_data.prediction_ids:
        ids = [int(x.strip()) for x in report_data.prediction_ids.split(",") if x.strip().isdigit()]
    else:
        # If no IDs provided, use the most recent prediction (optional)
        latest = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.timestamp.desc()).first()
        if latest:
            ids = [latest.id]
        else:
            raise HTTPException(status_code=404, detail="No predictions found for this user.")

    if not ids:
        raise HTTPException(status_code=400, detail="No valid prediction IDs provided.")

    # Fetch predictions (ensure they belong to the user)
    predictions = db.query(Prediction).filter(
        Prediction.id.in_(ids),
        Prediction.user_id == user.id
    ).all()
    if not predictions:
        raise HTTPException(status_code=404, detail="No valid predictions found.")

    # Prepare data for AI summary (dicts with required keys)
    pred_data = [
        {
            "result": p.result,
            "confidence": p.confidence,
            "timestamp": p.timestamp
        }
        for p in predictions
    ]

    # Generate AI summary
    summary = generate_ai_summary(pred_data)
    if not summary:
        summary = f"Patient has {len(predictions)} scans. Latest stage: {predictions[0].result if predictions else 'N/A'}."

    # Create PDF
    title = report_data.title or f"Report for {user.username} – {datetime.utcnow().strftime('%Y-%m-%d')}"
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{user.id}_{timestamp_str}.pdf"
    reports_dir = "static/reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, filename)

    generate_pdf_report(title, summary, pred_data, file_path)

    # Save report to database
    db_report = Report(
        user_id=user.id,
        title=title,
        summary=summary,
        file_path=file_path,
        prediction_ids=",".join(str(p['id']) for p in predictions),
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return {
        "message": "Report generated successfully",
        "report_id": db_report.id,
        "file_path": file_path
    }

@router.get(
    "/",
    response_model=List[ReportResponse],
    responses={401: {"description": "Unauthorized"}},
)
async def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List all reports for the authenticated user, newest first.
    """
    reports = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return reports

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    responses={
        404: {"description": "Report not found"},
        401: {"description": "Unauthorized"},
    },
)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get a specific report by ID, only if it belongs to the current user.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get(
    "/download/{report_id}",
    responses={
        404: {"description": "Report or file not found"},
        401: {"description": "Unauthorized"},
    },
)
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Download the PDF file for a specific report.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on server")
    return FileResponse(
        report.file_path,
        filename=os.path.basename(report.file_path),
        media_type='application/pdf'
    )