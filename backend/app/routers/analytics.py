"""Router for analytics endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Flight, TelemetrySummary, Drone
from app.services.analytics_service import AnalyticsService
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/analyze/{flight_id}")
async def analyze_flight(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """Run predictive analytics on a specific flight"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    analytics_service = AnalyticsService(db)
    alerts = analytics_service.analyze_flight_and_generate_alerts(flight_id)
    
    return {
        "success": True,
        "flight_id": flight_id,
        "alerts_generated": len(alerts),
        "alerts": [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "component": alert.component,
                "severity": alert.severity,
                "message": alert.message,
                "recommendation": alert.recommendation,
                "deviation_percent": alert.deviation_percent
            }
            for alert in alerts
        ]
    }


@router.get("/trends/motors/{drone_id}")
async def get_motor_trends(
    drone_id: int,
    motor_number: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get motor output trends for a drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    # Get recent flights with telemetry
    flights = (
        db.query(Flight)
        .filter(Flight.drone_id == drone_id)
        .order_by(desc(Flight.flight_date))
        .limit(limit)
        .all()
    )
    
    if not flights:
        return {"drone_id": drone_id, "trends": []}
    
    trends = []
    for flight in reversed(flights):  # Show chronological order
        if flight.telemetry_summary:
            ts = flight.telemetry_summary
            trend_data = {
                "flight_id": flight.id,
                "flight_date": flight.flight_date.isoformat(),
                "motors": {}
            }
            
            motor_range = [motor_number] if motor_number else range(1, 5)
            for m in motor_range:
                avg = getattr(ts, f'motor{m}_avg', None)
                max_val = getattr(ts, f'motor{m}_max', None)
                if avg or max_val:
                    trend_data["motors"][f"motor_{m}"] = {
                        "avg": avg,
                        "max": max_val
                    }
            
            trends.append(trend_data)
    
    return {
        "drone_id": drone_id,
        "drone_name": drone.name,
        "motor_number": motor_number,
        "trends": trends
    }


@router.get("/trends/battery/{drone_id}")
async def get_battery_trends(
    drone_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get battery health trends for a drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    flights = (
        db.query(Flight)
        .filter(Flight.drone_id == drone_id)
        .order_by(desc(Flight.flight_date))
        .limit(limit)
        .all()
    )
    
    if not flights:
        return {"drone_id": drone_id, "trends": []}
    
    trends = []
    for flight in reversed(flights):
        if flight.telemetry_summary:
            ts = flight.telemetry_summary
            trends.append({
                "flight_id": flight.id,
                "flight_date": flight.flight_date.isoformat(),
                "voltage_avg": ts.battery_voltage_avg,
                "voltage_min": ts.battery_voltage_min,
                "current_avg": ts.battery_current_avg,
                "current_max": ts.battery_current_max,
                "remaining_avg": ts.battery_remaining_avg,
                "internal_resistance_avg": ts.battery_internal_resistance_avg
            })
    
    return {
        "drone_id": drone_id,
        "drone_name": drone.name,
        "trends": trends
    }


@router.get("/trends/vibration/{drone_id}")
async def get_vibration_trends(
    drone_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get vibration trends for a drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    flights = (
        db.query(Flight)
        .filter(Flight.drone_id == drone_id)
        .order_by(desc(Flight.flight_date))
        .limit(limit)
        .all()
    )
    
    if not flights:
        return {"drone_id": drone_id, "trends": []}
    
    trends = []
    for flight in reversed(flights):
        if flight.telemetry_summary:
            ts = flight.telemetry_summary
            trends.append({
                "flight_id": flight.id,
                "flight_date": flight.flight_date.isoformat(),
                "magnitude_avg": ts.vibration_magnitude_avg,
                "magnitude_max": ts.vibration_magnitude_max,
                "x_avg": ts.vibration_x_avg,
                "y_avg": ts.vibration_y_avg,
                "z_avg": ts.vibration_z_avg
            })
    
    return {
        "drone_id": drone_id,
        "drone_name": drone.name,
        "trends": trends
    }


@router.get("/compare/{drone_id}")
async def compare_flights(
    drone_id: int,
    flight_id1: int,
    flight_id2: int,
    db: Session = Depends(get_db)
):
    """Compare two flights side by side"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    flight1 = db.query(Flight).filter(
        Flight.id == flight_id1,
        Flight.drone_id == drone_id
    ).first()
    flight2 = db.query(Flight).filter(
        Flight.id == flight_id2,
        Flight.drone_id == drone_id
    ).first()
    
    if not flight1:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id1} not found")
    if not flight2:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id2} not found")
    
    def extract_telemetry(flight):
        if not flight.telemetry_summary:
            return None
        ts = flight.telemetry_summary
        return {
            "flight_id": flight.id,
            "flight_date": flight.flight_date.isoformat(),
            "duration_seconds": flight.duration_seconds,
            "motors": {
                f"motor_{i}": {
                    "avg": getattr(ts, f'motor{i}_avg'),
                    "max": getattr(ts, f'motor{i}_max')
                }
                for i in range(1, 5)
            },
            "battery": {
                "voltage_avg": ts.battery_voltage_avg,
                "voltage_min": ts.battery_voltage_min,
                "current_avg": ts.battery_current_avg,
                "current_max": ts.battery_current_max,
                "remaining_avg": ts.battery_remaining_avg,
                "internal_resistance_avg": ts.battery_internal_resistance_avg
            },
            "vibration": {
                "magnitude_avg": ts.vibration_magnitude_avg,
                "magnitude_max": ts.vibration_magnitude_max,
                "x_avg": ts.vibration_x_avg,
                "y_avg": ts.vibration_y_avg,
                "z_avg": ts.vibration_z_avg
            }
        }
    
    return {
        "drone_id": drone_id,
        "drone_name": drone.name,
        "flight1": extract_telemetry(flight1),
        "flight2": extract_telemetry(flight2)
    }


@router.get("/statistics/{drone_id}")
async def get_drone_statistics(
    drone_id: int,
    db: Session = Depends(get_db)
):
    """Get overall statistics for a drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    # Get total flights
    total_flights = db.query(func.count(Flight.id)).filter(Flight.drone_id == drone_id).scalar()
    
    # Get total flight time
    total_time = db.query(func.sum(Flight.duration_seconds)).filter(Flight.drone_id == drone_id).scalar()
    
    # Get recent flights for averages
    recent_flights = (
        db.query(Flight)
        .filter(Flight.drone_id == drone_id)
        .order_by(desc(Flight.flight_date))
        .limit(10)
        .all()
    )
    
    # Calculate averages
    avg_stats = {}
    if recent_flights:
        motor_avgs = {i: [] for i in range(1, 5)}
        battery_voltage = []
        vibration_mag = []
        
        for flight in recent_flights:
            if flight.telemetry_summary:
                ts = flight.telemetry_summary
                for i in range(1, 5):
                    val = getattr(ts, f'motor{i}_avg')
                    if val:
                        motor_avgs[i].append(val)
                
                if ts.battery_voltage_avg:
                    battery_voltage.append(ts.battery_voltage_avg)
                if ts.vibration_magnitude_avg:
                    vibration_mag.append(ts.vibration_magnitude_avg)
        
        avg_stats = {
            "avg_motor_outputs": {
                f"motor_{i}": sum(vals) / len(vals) if vals else None
                for i, vals in motor_avgs.items()
            },
            "avg_battery_voltage": sum(battery_voltage) / len(battery_voltage) if battery_voltage else None,
            "avg_vibration_magnitude": sum(vibration_mag) / len(vibration_mag) if vibration_mag else None
        }
    
    return {
        "drone_id": drone_id,
        "drone_name": drone.name,
        "total_flights": total_flights,
        "total_flight_time_seconds": total_time or 0,
        "total_flight_time_hours": (total_time / 3600) if total_time else 0,
        "averages": avg_stats
    }
