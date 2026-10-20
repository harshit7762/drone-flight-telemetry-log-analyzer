"""Router for telemetry file upload and processing"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.telemetry_service import TelemetryService
from app.services.analytics_service import AnalyticsService
from config import get_settings
import os
import shutil
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/upload")
async def upload_telemetry_file(
    file: UploadFile = File(...),
    drone_id: str = Form(...),
    drone_name: Optional[str] = Form(None),
    run_analytics: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Upload and process a telemetry file (.bin or .tlog)
    
    Args:
        file: Telemetry file to upload
        drone_id: Unique identifier for the drone
        drone_name: Optional human-readable name for the drone
        run_analytics: Whether to run predictive analytics after processing
        db: Database session
    
    Returns:
        Processing results including flight ID and any generated alerts
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.bin', '.tlog']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only .bin and .tlog files are supported (got {file_ext})"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
        )
    
    # Save uploaded file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{drone_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved uploaded file: {file_path}")
        
        # Process telemetry file
        telemetry_service = TelemetryService(db)
        result = telemetry_service.process_telemetry_file(
            file_path=file_path,
            filename=file.filename,
            drone_id=drone_id,
            drone_name=drone_name
        )
        
        # Run predictive analytics if requested
        alerts = []
        if run_analytics and result.get("flight_id"):
            analytics_service = AnalyticsService(db)
            generated_alerts = analytics_service.analyze_flight_and_generate_alerts(
                result["flight_id"]
            )
            alerts = [
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "component": alert.component,
                    "severity": alert.severity,
                    "message": alert.message,
                    "recommendation": alert.recommendation
                }
                for alert in generated_alerts
            ]
        
        return {
            "success": True,
            "message": "Telemetry file processed successfully",
            "flight_id": result.get("flight_id"),
            "drone_id": result.get("drone_id"),
            "messages_processed": result.get("messages_processed"),
            "duration_seconds": result.get("duration_seconds"),
            "alerts_generated": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/validate-file/{filename}")
async def validate_file(filename: str):
    """Validate if a filename is acceptable"""
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ['.bin', '.tlog']:
        return {
            "valid": False,
            "error": f"Invalid file type. Only .bin and .tlog files are supported"
        }
    
    return {
        "valid": True,
        "file_type": file_ext.replace('.', '')
    }
