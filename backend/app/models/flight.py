from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Flight(Base):
    """Flight model representing individual flight sessions"""
    
    __tablename__ = "flights"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False, index=True)
    flight_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Float, nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(10), nullable=False)  # .bin or .tlog
    total_messages = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drone = relationship("Drone", back_populates="flights")
    telemetry_summary = relationship("TelemetrySummary", back_populates="flight", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Flight(id={self.id}, drone_id={self.drone_id}, date='{self.flight_date}')>"
