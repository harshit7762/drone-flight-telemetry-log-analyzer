"""Router for maintenance alert endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import MaintenanceAlert, Drone
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    drone_id: int
    drone_name: str
    flight_id: Optional[int]
    alert_type: str
    component: str
    severity: str
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_percent: float
    threshold_percent: float
    message: str
    recommendation: Optional[str]
    acknowledged: bool
    resolved: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    drone_id: Optional[int] = None,
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical)$"),
    alert_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """Get list of maintenance alerts with filters"""
    query = db.query(MaintenanceAlert).join(Drone)
    
    if drone_id:
        query = query.filter(MaintenanceAlert.drone_id == drone_id)
    if severity:
        query = query.filter(MaintenanceAlert.severity == severity)
    if alert_type:
        query = query.filter(MaintenanceAlert.alert_type == alert_type)
    if resolved is not None:
        query = query.filter(MaintenanceAlert.resolved == resolved)
    
    alerts = query.order_by(desc(MaintenanceAlert.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for alert in alerts:
        result.append({
            "id": alert.id,
            "drone_id": alert.drone_id,
            "drone_name": alert.drone.name,
            "flight_id": alert.flight_id,
            "alert_type": alert.alert_type,
            "component": alert.component,
            "severity": alert.severity,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "baseline_value": alert.baseline_value,
            "deviation_percent": alert.deviation_percent,
            "threshold_percent": alert.threshold_percent,
            "message": alert.message,
            "recommendation": alert.recommendation,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "created_at": alert.created_at.isoformat()
        })
    
    return result


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific alert"""
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "id": alert.id,
        "drone_id": alert.drone_id,
        "drone_name": alert.drone.name,
        "flight_id": alert.flight_id,
        "alert_type": alert.alert_type,
        "component": alert.component,
        "severity": alert.severity,
        "metric_name": alert.metric_name,
        "current_value": alert.current_value,
        "baseline_value": alert.baseline_value,
        "deviation_percent": alert.deviation_percent,
        "threshold_percent": alert.threshold_percent,
        "message": alert.message,
        "recommendation": alert.recommendation,
        "acknowledged": alert.acknowledged,
        "resolved": alert.resolved,
        "created_at": alert.created_at.isoformat()
    }


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Mark an alert as acknowledged"""
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Alert acknowledged",
        "alert_id": alert_id
    }


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Mark an alert as resolved"""
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Alert resolved",
        "alert_id": alert_id
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {
        "success": True,
        "message": f"Alert {alert_id} deleted successfully"
    }


@router.get("/summary/by-type")
async def get_alerts_by_type(
    drone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get summary of alerts grouped by type"""
    query = db.query(MaintenanceAlert)
    
    if drone_id:
        query = query.filter(MaintenanceAlert.drone_id == drone_id)
    
    alerts = query.filter(MaintenanceAlert.resolved == False).all()
    
    summary = {
        "motor": {"total": 0, "critical": 0, "warning": 0, "info": 0},
        "battery": {"total": 0, "critical": 0, "warning": 0, "info": 0},
        "vibration": {"total": 0, "critical": 0, "warning": 0, "info": 0}
    }
    
    for alert in alerts:
        if alert.alert_type in summary:
            summary[alert.alert_type]["total"] += 1
            summary[alert.alert_type][alert.severity] += 1
    
    return {
        "drone_id": drone_id,
        "unresolved_alerts": len(alerts),
        "by_type": summary
    }


@router.get("/summary/by-severity")
async def get_alerts_by_severity(
    drone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get summary of alerts grouped by severity"""
    query = db.query(MaintenanceAlert)
    
    if drone_id:
        query = query.filter(MaintenanceAlert.drone_id == drone_id)
    
    alerts = query.filter(MaintenanceAlert.resolved == False).all()
    
    summary = {
        "critical": [],
        "warning": [],
        "info": []
    }
    
    for alert in alerts:
        summary[alert.severity].append({
            "id": alert.id,
            "drone_id": alert.drone_id,
            "component": alert.component,
            "message": alert.message,
            "created_at": alert.created_at.isoformat()
        })
    
    return {
        "drone_id": drone_id,
        "total_unresolved": len(alerts),
        "critical_count": len(summary["critical"]),
        "warning_count": len(summary["warning"]),
        "info_count": len(summary["info"]),
        "alerts": summary
    }
