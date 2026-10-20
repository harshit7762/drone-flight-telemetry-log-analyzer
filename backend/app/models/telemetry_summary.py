from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class TelemetrySummary(Base):
    """Telemetry summary storing aggregated metrics for each flight"""
    
    __tablename__ = "telemetry_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), unique=True, nullable=False, index=True)
    
    # Motor Outputs (PWM values, typically 1000-2000 microseconds)
    motor1_avg = Column(Float, nullable=True)
    motor1_max = Column(Float, nullable=True)
    motor2_avg = Column(Float, nullable=True)
    motor2_max = Column(Float, nullable=True)
    motor3_avg = Column(Float, nullable=True)
    motor3_max = Column(Float, nullable=True)
    motor4_avg = Column(Float, nullable=True)
    motor4_max = Column(Float, nullable=True)
    
    # Battery Metrics
    battery_voltage_avg = Column(Float, nullable=True)
    battery_voltage_min = Column(Float, nullable=True)
    battery_current_avg = Column(Float, nullable=True)
    battery_current_max = Column(Float, nullable=True)
    battery_remaining_avg = Column(Float, nullable=True)  # Percentage
    battery_internal_resistance_avg = Column(Float, nullable=True)  # Internal resistance in mΩ (milliohms)
    battery_internal_resistance_min = Column(Float, nullable=True)  # in mΩ
    battery_internal_resistance_max = Column(Float, nullable=True)  # in mΩ
    
    # Individual cell voltages (for multi-cell batteries)
    cell_voltages = Column(JSON, nullable=True)  # Store as JSON array
    
    # IMU Vibration Readings (accelerometer)
    vibration_x_avg = Column(Float, nullable=True)
    vibration_x_max = Column(Float, nullable=True)
    vibration_y_avg = Column(Float, nullable=True)
    vibration_y_max = Column(Float, nullable=True)
    vibration_z_avg = Column(Float, nullable=True)
    vibration_z_max = Column(Float, nullable=True)
    
    # Overall vibration magnitude
    vibration_magnitude_avg = Column(Float, nullable=True)
    vibration_magnitude_max = Column(Float, nullable=True)
    
    # GPS and Altitude
    altitude_max = Column(Float, nullable=True)
    altitude_avg = Column(Float, nullable=True)
    speed_max = Column(Float, nullable=True)
    speed_avg = Column(Float, nullable=True)

    # GPS Signal Quality
    # gps_fix_count  = number of messages where GPS had a valid fix
    # total_gps_messages = total GPS-type messages seen in the flight
    # gps_fix_ratio  = gps_fix_count / total_gps_messages  (0.0 – 1.0)
    gps_fix_count = Column(Integer, nullable=True)
    total_gps_messages = Column(Integer, nullable=True)
    gps_fix_ratio = Column(Float, nullable=True)   # 1.0 = perfect lock throughout

    # Temperature
    temperature_avg = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    temperature_spike_count = Column(Integer, nullable=True)  # readings above spike threshold
    
    # Relationships
    flight = relationship("Flight", back_populates="telemetry_summary")
    
    def __repr__(self):
        return f"<TelemetrySummary(flight_id={self.flight_id})>"
