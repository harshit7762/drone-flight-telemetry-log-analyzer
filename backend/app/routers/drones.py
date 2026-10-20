"""Router for drone management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Drone, Flight, MaintenanceAlert
from app.services.analytics_service import AnalyticsService
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


class DroneResponse(BaseModel):
    id: int
    drone_id: str
    name: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    total_flights: int
    last_flight_date: Optional[str]
    
    class Config:
        from_attributes = True


class DroneDetailResponse(DroneResponse):
    health_status: str
    alert_counts: dict
    total_unresolved_alerts: int


@router.get("/", response_model=List[DroneResponse])
async def list_drones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of all drones"""
    drones = db.query(Drone).offset(skip).limit(limit).all()
    
    result = []
    for drone in drones:
        # Get flight count
        flight_count = db.query(func.count(Flight.id)).filter(Flight.drone_id == drone.id).scalar()
        
        # Get last flight date
        last_flight = db.query(Flight).filter(
            Flight.drone_id == drone.id
        ).order_by(Flight.flight_date.desc()).first()
        
        result.append({
            "id": drone.id,
            "drone_id": drone.drone_id,
            "name": drone.name,
            "model": drone.model,
            "serial_number": drone.serial_number,
            "total_flights": flight_count,
            "last_flight_date": last_flight.flight_date.isoformat() if last_flight else None
        })
    
    return result


@router.get("/{drone_id}", response_model=DroneDetailResponse)
async def get_drone(
    drone_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    # Get flight count
    flight_count = db.query(func.count(Flight.id)).filter(Flight.drone_id == drone.id).scalar()
    
    # Get last flight date
    last_flight = db.query(Flight).filter(
        Flight.drone_id == drone.id
    ).order_by(Flight.flight_date.desc()).first()
    
    # Get health summary
    analytics_service = AnalyticsService(db)
    health_summary = analytics_service.get_drone_health_summary(drone.id)
    
    return {
        "id": drone.id,
        "drone_id": drone.drone_id,
        "name": drone.name,
        "model": drone.model,
        "serial_number": drone.serial_number,
        "total_flights": flight_count,
        "last_flight_date": last_flight.flight_date.isoformat() if last_flight else None,
        "health_status": health_summary["health_status"],
        "alert_counts": health_summary["alert_counts"],
        "total_unresolved_alerts": health_summary["total_unresolved_alerts"]
    }


@router.get("/{drone_id}/health")
async def get_drone_health(
    drone_id: int,
    db: Session = Depends(get_db)
):
    """Get health summary for a drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_drone_health_summary(drone.id)


@router.put("/{drone_id}")
async def update_drone(
    drone_id: int,
    name: Optional[str] = None,
    model: Optional[str] = None,
    serial_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update drone information"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    if name is not None:
        drone.name = name
    if model is not None:
        drone.model = model
    if serial_number is not None:
        drone.serial_number = serial_number
    
    db.commit()
    db.refresh(drone)
    
    return {
        "success": True,
        "message": "Drone updated successfully",
        "drone": {
            "id": drone.id,
            "drone_id": drone.drone_id,
            "name": drone.name,
            "model": drone.model,
            "serial_number": drone.serial_number
        }
    }


@router.delete("/{drone_id}")
async def delete_drone(
    drone_id: int,
    db: Session = Depends(get_db)
):
    """Delete a drone and all associated data"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    db.delete(drone)
    db.commit()
    
    return {
        "success": True,
        "message": f"Drone {drone.drone_id} deleted successfully"
    }
