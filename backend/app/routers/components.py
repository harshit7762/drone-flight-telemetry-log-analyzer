"""Router for component management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Component, ComponentMaintenance, Drone
from app.services.component_service import ComponentService
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ComponentCreate(BaseModel):
    component_type: str  # "battery", "motor", "propeller", "esc"
    component_name: str
    serial_number: Optional[str] = None
    position: Optional[str] = None
    max_flight_hours: Optional[float] = None
    max_flight_count: Optional[int] = None
    max_cycles: Optional[int] = None


class ComponentResponse(BaseModel):
    id: int
    drone_id: int
    drone_name: str
    component_type: str
    component_name: str
    serial_number: Optional[str]
    position: Optional[str]
    is_active: bool
    total_flight_hours: float
    total_flight_count: int
    total_cycles: int
    max_flight_hours: Optional[float]
    max_flight_count: Optional[int]
    max_cycles: Optional[int]
    status: str
    health_percentage: Optional[float]
    installed_date: Optional[str]
    last_maintenance_date: Optional[str]
    
    class Config:
        from_attributes = True


class ComponentReplaceRequest(BaseModel):
    new_serial_number: Optional[str] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    cost: Optional[float] = None


@router.post("/register")
async def register_component(
    drone_id: int,
    component: ComponentCreate,
    db: Session = Depends(get_db)
):
    """Register a new component for a drone"""
    
    # Verify drone exists
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    service = ComponentService(db)
    
    new_component = service.register_component(
        drone_id=drone_id,
        component_type=component.component_type,
        component_name=component.component_name,
        serial_number=component.serial_number,
        position=component.position
    )
    
    # Override default limits if provided
    if component.max_flight_hours:
        new_component.max_flight_hours = component.max_flight_hours
    if component.max_flight_count:
        new_component.max_flight_count = component.max_flight_count
    if component.max_cycles:
        new_component.max_cycles = component.max_cycles
    
    db.commit()
    db.refresh(new_component)
    
    return {
        "success": True,
        "message": f"Component '{component.component_name}' registered successfully",
        "component_id": new_component.id
    }


@router.get("/drone/{drone_id}", response_model=List[ComponentResponse])
async def get_drone_components(
    drone_id: int,
    active_only: bool = Query(default=True),
    component_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all components for a drone"""
    
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    service = ComponentService(db)
    components = service.get_drone_components(drone_id, active_only=active_only)
    
    # Filter by type if specified
    if component_type:
        components = [c for c in components if c.component_type == component_type]
    
    result = []
    for comp in components:
        result.append({
            "id": comp.id,
            "drone_id": comp.drone_id,
            "drone_name": drone.name or drone.drone_id,
            "component_type": comp.component_type,
            "component_name": comp.component_name,
            "serial_number": comp.serial_number,
            "position": comp.position,
            "is_active": comp.is_active,
            "total_flight_hours": comp.total_flight_hours,
            "total_flight_count": comp.total_flight_count,
            "total_cycles": comp.total_cycles,
            "max_flight_hours": comp.max_flight_hours,
            "max_flight_count": comp.max_flight_count,
            "max_cycles": comp.max_cycles,
            "status": comp.status,
            "health_percentage": comp.health_percentage,
            "installed_date": comp.installed_date.isoformat() if comp.installed_date else None,
            "last_maintenance_date": comp.last_maintenance_date.isoformat() if comp.last_maintenance_date else None
        })
    
    return result


@router.get("/{component_id}")
async def get_component_details(
    component_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a component including maintenance history"""
    
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    service = ComponentService(db)
    maintenance_history = service.get_component_maintenance_history(component_id)
    
    return {
        "id": component.id,
        "drone_id": component.drone_id,
        "component_type": component.component_type,
        "component_name": component.component_name,
        "serial_number": component.serial_number,
        "position": component.position,
        "is_active": component.is_active,
        "installed_date": component.installed_date.isoformat() if component.installed_date else None,
        "removed_date": component.removed_date.isoformat() if component.removed_date else None,
        "total_flight_hours": component.total_flight_hours,
        "total_flight_count": component.total_flight_count,
        "total_cycles": component.total_cycles,
        "max_flight_hours": component.max_flight_hours,
        "max_flight_count": component.max_flight_count,
        "max_cycles": component.max_cycles,
        "status": component.status,
        "health_percentage": component.health_percentage,
        "last_maintenance_date": component.last_maintenance_date.isoformat() if component.last_maintenance_date else None,
        "notes": component.notes,
        "maintenance_history": [
            {
                "id": m.id,
                "maintenance_type": m.maintenance_type,
                "maintenance_date": m.maintenance_date.isoformat(),
                "performed_by": m.performed_by,
                "notes": m.notes,
                "flight_hours_at_maintenance": m.flight_hours_at_maintenance,
                "cycles_at_maintenance": m.cycles_at_maintenance,
                "cost": m.cost
            }
            for m in maintenance_history
        ]
    }


@router.post("/{component_id}/replace")
async def replace_component(
    component_id: int,
    request: ComponentReplaceRequest,
    db: Session = Depends(get_db)
):
    """Mark a component as replaced and create a new one"""
    
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    service = ComponentService(db)
    
    new_component = service.replace_component(
        component_id=component_id,
        new_serial_number=request.new_serial_number,
        notes=request.notes,
        performed_by=request.performed_by,
        cost=request.cost
    )
    
    return {
        "success": True,
        "message": f"Component '{component.component_name}' replaced successfully",
        "old_component_id": component_id,
        "new_component_id": new_component.id,
        "old_usage": {
            "flight_hours": component.total_flight_hours,
            "flight_count": component.total_flight_count,
            "cycles": component.total_cycles
        }
    }


@router.delete("/{component_id}")
async def delete_component(
    component_id: int,
    db: Session = Depends(get_db)
):
    """Delete a component (marks as inactive)"""
    
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    component.is_active = False
    component.removed_date = datetime.utcnow()
    component.status = "removed"
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Component '{component.component_name}' marked as inactive"
    }


@router.get("/fleet/summary")
async def get_fleet_component_summary(db: Session = Depends(get_db)):
    """Get summary of all components across the fleet"""
    
    service = ComponentService(db)
    summary = service.get_fleet_component_summary()
    
    return summary


@router.put("/{component_id}")
async def update_component(
    component_id: int,
    serial_number: Optional[str] = None,
    notes: Optional[str] = None,
    max_flight_hours: Optional[float] = None,
    max_flight_count: Optional[int] = None,
    max_cycles: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update component information"""
    
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    if serial_number is not None:
        component.serial_number = serial_number
    if notes is not None:
        component.notes = notes
    if max_flight_hours is not None:
        component.max_flight_hours = max_flight_hours
    if max_flight_count is not None:
        component.max_flight_count = max_flight_count
    if max_cycles is not None:
        component.max_cycles = max_cycles
    
    # Recalculate health after updating limits
    component.update_status()
    
    db.commit()
    db.refresh(component)
    
    return {
        "success": True,
        "message": "Component updated successfully",
        "component": {
            "id": component.id,
            "component_name": component.component_name,
            "status": component.status,
            "health_percentage": component.health_percentage
        }
    }
