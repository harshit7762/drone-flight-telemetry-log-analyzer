"""
Component Service for managing hardware component lifecycles
Tracks batteries, motors, propellers, ESCs, etc.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Optional
from datetime import datetime
from app.models import Component, ComponentMaintenance, Flight, Drone, MaintenanceAlert
import logging

logger = logging.getLogger(__name__)

# Default component lifecycle limits (in flight hours and cycles)
COMPONENT_DEFAULTS = {
    "battery": {
        "max_cycles": 300,
        "max_flight_hours": 150,
        "max_flight_count": 300
    },
    "motor": {
        "max_flight_hours": 300,
        "max_flight_count": 1000
    },
    "propeller": {
        "max_flight_hours": 50,
        "max_flight_count": 200
    },
    "esc": {
        "max_flight_hours": 500,
        "max_flight_count": 1000
    }
}


class ComponentService:
    """Service for managing component lifecycles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_component(
        self,
        drone_id: int,
        component_type: str,
        component_name: str,
        serial_number: Optional[str] = None,
        position: Optional[str] = None,
        installed_date: Optional[datetime] = None
    ) -> Component:
        """Register a new component for a drone"""
        
        # Get default limits for this component type
        defaults = COMPONENT_DEFAULTS.get(component_type, {})
        
        component = Component(
            drone_id=drone_id,
            component_type=component_type,
            component_name=component_name,
            serial_number=serial_number,
            position=position,
            installed_date=installed_date or datetime.utcnow(),
            is_active=True,
            max_flight_hours=defaults.get("max_flight_hours"),
            max_flight_count=defaults.get("max_flight_count"),
            max_cycles=defaults.get("max_cycles"),
            status="good",
            health_percentage=100.0
        )
        
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        
        logger.info(f"Registered {component_type} '{component_name}' for drone {drone_id}")
        
        return component
    
    def update_component_usage_after_flight(self, flight_id: int):
        """Update all active components' usage counters after a flight"""
        
        flight = self.db.query(Flight).filter(Flight.id == flight_id).first()
        if not flight:
            return
        
        # Get all active components for this drone
        components = self.db.query(Component).filter(
            Component.drone_id == flight.drone_id,
            Component.is_active == True
        ).all()
        
        if not components:
            logger.info(f"No components registered for drone {flight.drone_id}")
            return
        
        flight_hours = (flight.duration_seconds or 0) / 3600.0
        
        for component in components:
            # Update usage counters
            component.total_flight_hours += flight_hours
            component.total_flight_count += 1
            
            # For batteries, also increment cycle count
            if component.component_type == "battery":
                component.total_cycles += 1
            
            # Update health and status
            component.update_status()
            
            logger.debug(
                f"Updated {component.component_name}: "
                f"{component.total_flight_hours:.1f}h, "
                f"{component.total_flight_count} flights, "
                f"{component.total_cycles} cycles"
            )
        
        self.db.commit()
        
        # Check if any components need alerts
        self._check_component_alerts(flight.drone_id)
    
    def _check_component_alerts(self, drone_id: int):
        """Generate maintenance alerts for components nearing limits"""
        
        components = self.db.query(Component).filter(
            Component.drone_id == drone_id,
            Component.is_active == True
        ).all()
        
        for component in components:
            health = component.health_percentage or 100
            
            # Generate alerts at 25%, 10%, and 0% health
            if health <= 10:
                self._create_component_alert(
                    component,
                    "critical",
                    f"{component.component_name} is OVERDUE for replacement ({health:.0f}% life remaining)"
                )
            elif health <= 25:
                self._create_component_alert(
                    component,
                    "warning",
                    f"{component.component_name} should be replaced soon ({health:.0f}% life remaining)"
                )
    
    def _create_component_alert(self, component: Component, severity: str, message: str):
        """Create a maintenance alert for a component"""
        
        # Check if alert already exists
        existing_alert = self.db.query(MaintenanceAlert).filter(
            MaintenanceAlert.drone_id == component.drone_id,
            MaintenanceAlert.component == component.component_name,
            MaintenanceAlert.alert_type == "component_lifecycle",
            MaintenanceAlert.resolved == False
        ).first()
        
        if existing_alert:
            # Update existing alert
            existing_alert.severity = severity
            existing_alert.message = message
            existing_alert.current_value = component.health_percentage or 0
        else:
            # Create new alert
            alert = MaintenanceAlert(
                drone_id=component.drone_id,
                alert_type="component_lifecycle",
                component=component.component_name,
                severity=severity,
                metric_name=f"{component.component_type}_usage",
                current_value=component.health_percentage or 0,
                baseline_value=100.0,
                deviation_percent=100 - (component.health_percentage or 0),
                threshold_percent=75.0,
                message=message,
                recommendation=self._get_component_recommendation(component)
            )
            self.db.add(alert)
        
        self.db.commit()
    
    def _get_component_recommendation(self, component: Component) -> str:
        """Get maintenance recommendation for a component"""
        
        recommendations = {
            "battery": (
                f"Replace battery '{component.component_name}'. "
                f"Current usage: {component.total_cycles} cycles / {component.max_cycles} max, "
                f"{component.total_flight_hours:.1f}h / {component.max_flight_hours}h max. "
                "Order replacement battery and schedule swap during next maintenance window."
            ),
            "motor": (
                f"Inspect or replace motor '{component.component_name}'. "
                f"Current usage: {component.total_flight_hours:.1f}h / {component.max_flight_hours}h max. "
                "Check bearings for wear, test motor temperatures, inspect windings for damage."
            ),
            "propeller": (
                f"Replace propeller '{component.component_name}'. "
                f"Current usage: {component.total_flight_hours:.1f}h / {component.max_flight_hours}h max. "
                "Inspect for cracks, chips, or imbalance. Replace entire propeller set for best performance."
            ),
            "esc": (
                f"Inspect ESC '{component.component_name}'. "
                f"Current usage: {component.total_flight_hours:.1f}h / {component.max_flight_hours}h max. "
                "Check for overheating, test output signals, inspect solder joints."
            )
        }
        
        return recommendations.get(component.component_type, "Schedule maintenance inspection.")
    
    def replace_component(
        self,
        component_id: int,
        new_serial_number: Optional[str] = None,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None,
        cost: Optional[float] = None
    ) -> Component:
        """Mark component as replaced and create new component entry"""
        
        old_component = self.db.query(Component).filter(Component.id == component_id).first()
        if not old_component:
            raise ValueError(f"Component {component_id} not found")
        
        # Mark old component as inactive
        old_component.is_active = False
        old_component.removed_date = datetime.utcnow()
        old_component.status = "replaced"
        
        # Create maintenance log
        maintenance_log = ComponentMaintenance(
            component_id=component_id,
            maintenance_type="replaced",
            maintenance_date=datetime.utcnow(),
            performed_by=performed_by,
            notes=notes,
            flight_hours_at_maintenance=old_component.total_flight_hours,
            flight_count_at_maintenance=old_component.total_flight_count,
            cycles_at_maintenance=old_component.total_cycles,
            cost=cost
        )
        self.db.add(maintenance_log)
        
        # Create new component
        new_component = Component(
            drone_id=old_component.drone_id,
            component_type=old_component.component_type,
            component_name=old_component.component_name,
            serial_number=new_serial_number or f"{old_component.serial_number}-NEW",
            position=old_component.position,
            installed_date=datetime.utcnow(),
            is_active=True,
            max_flight_hours=old_component.max_flight_hours,
            max_flight_count=old_component.max_flight_count,
            max_cycles=old_component.max_cycles,
            status="good",
            health_percentage=100.0
        )
        self.db.add(new_component)
        self.db.flush()
        
        # Link maintenance log to new component
        maintenance_log.new_component_id = new_component.id
        
        # Resolve any lifecycle alerts for this component
        self.db.query(MaintenanceAlert).filter(
            MaintenanceAlert.drone_id == old_component.drone_id,
            MaintenanceAlert.component == old_component.component_name,
            MaintenanceAlert.alert_type == "component_lifecycle",
            MaintenanceAlert.resolved == False
        ).update({"resolved": True, "resolved_at": datetime.utcnow()})
        
        self.db.commit()
        self.db.refresh(new_component)
        
        logger.info(f"Replaced {old_component.component_name} (ID: {component_id}) with new component (ID: {new_component.id})")
        
        return new_component
    
    def get_drone_components(self, drone_id: int, active_only: bool = True) -> List[Component]:
        """Get all components for a drone"""
        query = self.db.query(Component).filter(Component.drone_id == drone_id)
        
        if active_only:
            query = query.filter(Component.is_active == True)
        
        return query.order_by(Component.component_type, Component.component_name).all()
    
    def get_component_maintenance_history(self, component_id: int) -> List[ComponentMaintenance]:
        """Get maintenance history for a component"""
        return (
            self.db.query(ComponentMaintenance)
            .filter(ComponentMaintenance.component_id == component_id)
            .order_by(desc(ComponentMaintenance.maintenance_date))
            .all()
        )
    
    def get_fleet_component_summary(self) -> Dict:
        """Get summary of all components across the fleet"""
        
        components = self.db.query(Component).filter(Component.is_active == True).all()
        
        summary = {
            "total_components": len(components),
            "by_type": {},
            "by_status": {
                "good": 0,
                "attention": 0,
                "replace_soon": 0,
                "overdue": 0
            },
            "components_needing_attention": []
        }
        
        for component in components:
            # Count by type
            component_type = component.component_type
            if component_type not in summary["by_type"]:
                summary["by_type"][component_type] = 0
            summary["by_type"][component_type] += 1
            
            # Count by status
            status = component.status or "good"
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Track components needing attention
            if status in ["attention", "replace_soon", "overdue"]:
                summary["components_needing_attention"].append({
                    "id": component.id,
                    "drone_id": component.drone_id,
                    "type": component.component_type,
                    "name": component.component_name,
                    "status": status,
                    "health_percentage": component.health_percentage
                })
        
        return summary
