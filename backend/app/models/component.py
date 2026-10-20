from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Component(Base):
    """Component model for tracking individual hardware components"""
    
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False, index=True)
    
    # Component identification
    component_type = Column(String(50), nullable=False, index=True)  # "battery", "motor", "propeller", "esc"
    component_name = Column(String(100), nullable=False)  # "Battery-001", "Motor Front Left", etc.
    serial_number = Column(String(100), nullable=True)
    position = Column(String(50), nullable=True)  # "front_left", "front_right", "rear_left", "rear_right"
    
    # Installation tracking
    installed_date = Column(DateTime(timezone=True), nullable=True)
    removed_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage tracking
    total_flight_hours = Column(Float, default=0.0)
    total_flight_count = Column(Integer, default=0)
    total_cycles = Column(Integer, default=0)  # For batteries: charge/discharge cycles
    
    # Lifecycle limits (recommended replacement thresholds)
    max_flight_hours = Column(Float, nullable=True)
    max_flight_count = Column(Integer, nullable=True)
    max_cycles = Column(Integer, nullable=True)  # For batteries
    
    # Status and health
    status = Column(String(20), default="good", index=True)  # "good", "attention", "replace_soon", "overdue", "replaced"
    health_percentage = Column(Float, nullable=True)  # 0-100%
    
    # Maintenance
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    drone = relationship("Drone", back_populates="components")
    maintenance_logs = relationship("ComponentMaintenance", back_populates="component", cascade="all, delete-orphan", foreign_keys="ComponentMaintenance.component_id")
    
    def __repr__(self):
        return f"<Component(type='{self.component_type}', name='{self.component_name}', status='{self.status}')>"
    
    def calculate_health_percentage(self):
        """Calculate health percentage based on usage vs limits"""
        percentages = []
        
        if self.max_flight_hours and self.total_flight_hours:
            percentages.append((self.total_flight_hours / self.max_flight_hours) * 100)
        
        if self.max_flight_count and self.total_flight_count:
            percentages.append((self.total_flight_count / self.max_flight_count) * 100)
        
        if self.max_cycles and self.total_cycles:
            percentages.append((self.total_cycles / self.max_cycles) * 100)
        
        if percentages:
            usage_percent = max(percentages)  # Use worst case
            return 100 - usage_percent  # Health = 100% - usage%
        
        return 100.0
    
    def update_status(self):
        """Update component status based on usage"""
        health = self.calculate_health_percentage()
        self.health_percentage = health
        
        if health <= 10:
            self.status = "overdue"
        elif health <= 25:
            self.status = "replace_soon"
        elif health <= 50:
            self.status = "attention"
        else:
            self.status = "good"


class ComponentMaintenance(Base):
    """Maintenance log for components"""
    
    __tablename__ = "component_maintenance"
    
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=False, index=True)
    
    maintenance_type = Column(String(50), nullable=False)  # "replaced", "inspected", "repaired", "cleaned"
    maintenance_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    performed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # If replacement, track what was replaced with
    new_component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    
    # Usage at time of maintenance
    flight_hours_at_maintenance = Column(Float, nullable=True)
    flight_count_at_maintenance = Column(Integer, nullable=True)
    cycles_at_maintenance = Column(Integer, nullable=True)
    
    # Cost tracking
    cost = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    component = relationship("Component", back_populates="maintenance_logs", foreign_keys=[component_id])
    
    def __repr__(self):
        return f"<ComponentMaintenance(type='{self.maintenance_type}', date='{self.maintenance_date}')>"
