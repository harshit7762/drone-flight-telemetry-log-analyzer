from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MaintenanceAlert(Base):
    """Maintenance alert model for predictive warnings"""
    
    __tablename__ = "maintenance_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=True, index=True)
    
    alert_type = Column(String(50), nullable=False, index=True)  # e.g., "motor", "battery", "vibration"
    component = Column(String(100), nullable=False)  # e.g., "motor_1", "battery", "imu"
    severity = Column(String(20), nullable=False, default="warning")  # "info", "warning", "critical"
    
    metric_name = Column(String(100), nullable=False)
    current_value = Column(Float, nullable=False)
    baseline_value = Column(Float, nullable=False)
    deviation_percent = Column(Float, nullable=False)
    threshold_percent = Column(Float, nullable=False)
    
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    drone = relationship("Drone", back_populates="maintenance_alerts")
    
    def __repr__(self):
        return f"<MaintenanceAlert(id={self.id}, type='{self.alert_type}', component='{self.component}', severity='{self.severity}')>"
