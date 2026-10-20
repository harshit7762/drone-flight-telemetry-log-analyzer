"""Router for flight data endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Flight, TelemetrySummary, Drone
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


def check_is_ground_only(ts) -> bool:
    """A flight is considered ground-only if no motor ever ran above idle (1050 µs)
    or all motor averages are None (new parser) or <= 1050 (old logs with 1000 µs idle).
    """
    if not ts:
        return False
    motor_maxes = [ts.motor1_max, ts.motor2_max, ts.motor3_max, ts.motor4_max]
    if all(m is None for m in motor_maxes):
        return True
    return all((m or 0) <= 1050 for m in motor_maxes)


def get_gps_health_status(fix_count: Optional[int], total_messages: Optional[int], ratio: Optional[float]) -> dict:
    """
    Evaluate GPS signal reception quality and packet reception.
    Returns status ('ok', 'degraded', 'no_fix', 'no_data'), label, and detailed message.
    """
    if total_messages is None or total_messages == 0:
        return {
            "status": "no_data",
            "label": "No GPS Data",
            "message": "No GPS telemetry packets recorded in this flight log."
        }

    cnt = fix_count if fix_count is not None else 0
    if ratio is None or cnt == 0:
        return {
            "status": "no_fix",
            "label": "No 3D Fix",
            "message": f"GPS signal lost or no 3D lock. 0 out of {total_messages} packets had a valid fix."
        }

    pct = round(ratio * 100, 1)
    if ratio >= 0.90:
        return {
            "status": "ok",
            "label": "GPS OK - Healthy",
            "message": f"GPS is working correctly & fine. {cnt} out of {total_messages} packets received with valid 3D fix ({pct}%)."
        }
    else:
        lost = total_messages - cnt
        loss_pct = round((1.0 - ratio) * 100, 1)
        return {
            "status": "degraded",
            "label": "Degraded - Packet Loss",
            "message": f"Packets are not being received correctly! {lost} packets dropped ({loss_pct}% loss). Only {cnt} out of {total_messages} packets received with valid fix ({pct}%)."
        }



class FlightSummary(BaseModel):
    id: int
    drone_id: int
    drone_name: str
    flight_date: str
    duration_seconds: Optional[float]
    filename: str
    file_type: str
    total_messages: int
    is_ground_only: Optional[bool] = False
    gps_status: Optional[str] = None
    gps_fix_ratio: Optional[float] = None
    
    class Config:
        from_attributes = True


class TelemetryData(BaseModel):
    is_ground_only: Optional[bool] = False
    motor1_avg: Optional[float]
    motor1_max: Optional[float]
    motor2_avg: Optional[float]
    motor2_max: Optional[float]
    motor3_avg: Optional[float]
    motor3_max: Optional[float]
    motor4_avg: Optional[float]
    motor4_max: Optional[float]
    battery_voltage_avg: Optional[float]
    battery_voltage_min: Optional[float]
    battery_current_avg: Optional[float]
    battery_current_max: Optional[float]
    battery_remaining_avg: Optional[float]
    battery_internal_resistance_avg: Optional[float]
    battery_internal_resistance_min: Optional[float]
    battery_internal_resistance_max: Optional[float]
    cell_voltages: Optional[dict]
    vibration_x_avg: Optional[float]
    vibration_x_max: Optional[float]
    vibration_y_avg: Optional[float]
    vibration_y_max: Optional[float]
    vibration_z_avg: Optional[float]
    vibration_z_max: Optional[float]
    vibration_magnitude_avg: Optional[float]
    vibration_magnitude_max: Optional[float]
    altitude_max: Optional[float]
    altitude_avg: Optional[float]
    speed_max: Optional[float]
    speed_avg: Optional[float]
    temperature_avg: Optional[float]
    temperature_max: Optional[float]
    # GPS Fix & Packet Reception Metrics
    gps_fix_count: Optional[int] = None
    total_gps_messages: Optional[int] = None
    gps_fix_ratio: Optional[float] = None
    gps_status: Optional[str] = None
    gps_status_label: Optional[str] = None
    gps_status_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class FlightDetail(FlightSummary):
    telemetry: Optional[TelemetryData]


@router.get("/", response_model=List[FlightSummary])
async def list_flights(
    drone_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """Get list of flights, optionally filtered by drone"""
    query = db.query(Flight).join(Drone)
    
    if drone_id:
        query = query.filter(Flight.drone_id == drone_id)
    
    flights = query.order_by(desc(Flight.flight_date)).offset(skip).limit(limit).all()
    
    result = []
    for flight in flights:
        ts = flight.telemetry_summary
        is_ground = check_is_ground_only(ts) if ts else False
        gps_info = get_gps_health_status(ts.gps_fix_count, ts.total_gps_messages, ts.gps_fix_ratio) if ts else {}
        result.append({
            "id": flight.id,
            "drone_id": flight.drone_id,
            "drone_name": flight.drone.name,
            "flight_date": flight.flight_date.isoformat(),
            "duration_seconds": flight.duration_seconds,
            "filename": flight.filename,
            "file_type": flight.file_type,
            "total_messages": flight.total_messages,
            "is_ground_only": is_ground,
            "gps_status": gps_info.get("status"),
            "gps_fix_ratio": ts.gps_fix_ratio if ts else None
        })
    
    return result


@router.get("/{flight_id}", response_model=FlightDetail)
async def get_flight(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific flight"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    telemetry_data = None
    is_ground = False
    if flight.telemetry_summary:
        ts = flight.telemetry_summary
        is_ground = check_is_ground_only(ts)
        gps_info = get_gps_health_status(ts.gps_fix_count, ts.total_gps_messages, ts.gps_fix_ratio)
        telemetry_data = {
            "is_ground_only": is_ground,
            "motor1_avg": ts.motor1_avg,
            "motor1_max": ts.motor1_max,
            "motor2_avg": ts.motor2_avg,
            "motor2_max": ts.motor2_max,
            "motor3_avg": ts.motor3_avg,
            "motor3_max": ts.motor3_max,
            "motor4_avg": ts.motor4_avg,
            "motor4_max": ts.motor4_max,
            "battery_voltage_avg": ts.battery_voltage_avg,
            "battery_voltage_min": ts.battery_voltage_min,
            "battery_current_avg": ts.battery_current_avg,
            "battery_current_max": ts.battery_current_max,
            "battery_remaining_avg": ts.battery_remaining_avg,
            "battery_internal_resistance_avg": ts.battery_internal_resistance_avg,
            "battery_internal_resistance_min": ts.battery_internal_resistance_min,
            "battery_internal_resistance_max": ts.battery_internal_resistance_max,
            "cell_voltages": ts.cell_voltages,
            "vibration_x_avg": ts.vibration_x_avg,
            "vibration_x_max": ts.vibration_x_max,
            "vibration_y_avg": ts.vibration_y_avg,
            "vibration_y_max": ts.vibration_y_max,
            "vibration_z_avg": ts.vibration_z_avg,
            "vibration_z_max": ts.vibration_z_max,
            "vibration_magnitude_avg": ts.vibration_magnitude_avg,
            "vibration_magnitude_max": ts.vibration_magnitude_max,
            "altitude_max": ts.altitude_max,
            "altitude_avg": ts.altitude_avg,
            "speed_max": ts.speed_max,
            "speed_avg": ts.speed_avg,
            "temperature_avg": ts.temperature_avg,
            "temperature_max": ts.temperature_max,
            # GPS Fix & Packet Reception Metrics
            "gps_fix_count": ts.gps_fix_count,
            "total_gps_messages": ts.total_gps_messages,
            "gps_fix_ratio": ts.gps_fix_ratio,
            "gps_status": gps_info["status"],
            "gps_status_label": gps_info["label"],
            "gps_status_message": gps_info["message"]
        }
    
    return {
        "id": flight.id,
        "drone_id": flight.drone_id,
        "drone_name": flight.drone.name,
        "flight_date": flight.flight_date.isoformat(),
        "duration_seconds": flight.duration_seconds,
        "filename": flight.filename,
        "file_type": flight.file_type,
        "total_messages": flight.total_messages,
        "is_ground_only": is_ground,
        "telemetry": telemetry_data
    }


@router.get("/{flight_id}/telemetry", response_model=TelemetryData)
async def get_flight_telemetry(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """Get telemetry data for a specific flight"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    if not flight.telemetry_summary:
        raise HTTPException(status_code=404, detail="No telemetry data for this flight")
    
    ts = flight.telemetry_summary
    is_ground = check_is_ground_only(ts)
    gps_info = get_gps_health_status(ts.gps_fix_count, ts.total_gps_messages, ts.gps_fix_ratio)
    data = {c.name: getattr(ts, c.name) for c in ts.__table__.columns}
    data["is_ground_only"] = is_ground
    data["gps_status"] = gps_info["status"]
    data["gps_status_label"] = gps_info["label"]
    data["gps_status_message"] = gps_info["message"]
    return data


@router.delete("/{flight_id}")
async def delete_flight(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """Delete a flight and its telemetry data"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Delete file if it exists
    import os
    if flight.file_path and os.path.exists(flight.file_path):
        try:
            os.remove(flight.file_path)
        except Exception as e:
            pass  # Continue even if file deletion fails
    
    db.delete(flight)
    db.commit()
    
    return {
        "success": True,
        "message": f"Flight {flight_id} deleted successfully"
    }
