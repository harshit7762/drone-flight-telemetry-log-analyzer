from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Drone(Base):
    """Drone model representing individual drones"""
    
    __tablename__ = "drones"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    flights = relationship("Flight", back_populates="drone", cascade="all, delete-orphan")
    maintenance_alerts = relationship("MaintenanceAlert", back_populates="drone", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="drone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Drone(drone_id='{self.drone_id}', name='{self.name}')>"
