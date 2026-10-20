"""Service for processing telemetry files and storing data"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Optional
import os
import shutil
from app.models import Drone, Flight, TelemetrySummary
from app.utils.telemetry_parser import parse_telemetry_file
import logging

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service for handling telemetry file uploads and processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_telemetry_file(
        self,
        file_path: str,
        filename: str,
        drone_id: str,
        drone_name: Optional[str] = None
    ) -> Dict:
        """
        Process uploaded telemetry file and store results in database
        
        Args:
            file_path: Path to uploaded file
            filename: Original filename
            drone_id: Unique identifier for the drone
            drone_name: Optional human-readable name for the drone
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Get or create drone
            drone = self._get_or_create_drone(drone_id, drone_name)
            
            # Parse telemetry file
            logger.info(f"Parsing telemetry file: {filename}")
            telemetry_stats = parse_telemetry_file(file_path)
            
            # Determine file type
            file_ext = os.path.splitext(filename)[1].lower()
            file_type = file_ext.replace('.', '')
            
            # Create flight record
            flight_date = datetime.now()
            if telemetry_stats.get('flight_start_time'):
                try:
                    flight_date = datetime.fromtimestamp(telemetry_stats['flight_start_time'])
                except:
                    pass
            
            flight = Flight(
                drone_id=drone.id,
                flight_date=flight_date,
                duration_seconds=telemetry_stats.get('duration_seconds'),
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                total_messages=telemetry_stats.get('total_messages', 0)
            )
            self.db.add(flight)
            self.db.flush()  # Get flight ID
            
            # Create telemetry summary
            telemetry_summary = TelemetrySummary(
                flight_id=flight.id,
                motor1_avg=telemetry_stats.get('motor1_avg'),
                motor1_max=telemetry_stats.get('motor1_max'),
                motor2_avg=telemetry_stats.get('motor2_avg'),
                motor2_max=telemetry_stats.get('motor2_max'),
                motor3_avg=telemetry_stats.get('motor3_avg'),
                motor3_max=telemetry_stats.get('motor3_max'),
                motor4_avg=telemetry_stats.get('motor4_avg'),
                motor4_max=telemetry_stats.get('motor4_max'),
                battery_voltage_avg=telemetry_stats.get('battery_voltage_avg'),
                battery_voltage_min=telemetry_stats.get('battery_voltage_min'),
                battery_current_avg=telemetry_stats.get('battery_current_avg'),
                battery_current_max=telemetry_stats.get('battery_current_max'),
                battery_remaining_avg=telemetry_stats.get('battery_remaining_avg'),
                battery_internal_resistance_avg=telemetry_stats.get('battery_internal_resistance_avg'),
                battery_internal_resistance_min=telemetry_stats.get('battery_internal_resistance_min'),
                battery_internal_resistance_max=telemetry_stats.get('battery_internal_resistance_max'),
                cell_voltages=telemetry_stats.get('cell_voltages'),
                vibration_x_avg=telemetry_stats.get('vibration_x_avg'),
                vibration_x_max=telemetry_stats.get('vibration_x_max'),
                vibration_y_avg=telemetry_stats.get('vibration_y_avg'),
                vibration_y_max=telemetry_stats.get('vibration_y_max'),
                vibration_z_avg=telemetry_stats.get('vibration_z_avg'),
                vibration_z_max=telemetry_stats.get('vibration_z_max'),
                vibration_magnitude_avg=telemetry_stats.get('vibration_magnitude_avg'),
                vibration_magnitude_max=telemetry_stats.get('vibration_magnitude_max'),
                altitude_max=telemetry_stats.get('altitude_max'),
                altitude_avg=telemetry_stats.get('altitude_avg'),
                speed_max=telemetry_stats.get('speed_max'),
                speed_avg=telemetry_stats.get('speed_avg'),
                temperature_avg=telemetry_stats.get('temperature_avg'),
                temperature_max=telemetry_stats.get('temperature_max'),
                # GPS fix quality
                gps_fix_count=telemetry_stats.get('gps_fix_count'),
                total_gps_messages=telemetry_stats.get('total_gps_messages'),
                gps_fix_ratio=telemetry_stats.get('gps_fix_ratio'),
                # Temperature spike count
                temperature_spike_count=telemetry_stats.get('temperature_spike_count'),
            )
            self.db.add(telemetry_summary)
            self.db.commit()
            
            # Update component usage (if components are registered)
            from app.services.component_service import ComponentService
            component_service = ComponentService(self.db)
            component_service.update_component_usage_after_flight(flight.id)
            
            logger.info(f"Successfully processed flight {flight.id} for drone {drone_id}")
            
            return {
                "success": True,
                "flight_id": flight.id,
                "drone_id": drone.id,
                "messages_processed": telemetry_stats.get('total_messages', 0),
                "duration_seconds": telemetry_stats.get('duration_seconds')
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing telemetry file: {str(e)}")
            raise
    
    def _get_or_create_drone(self, drone_id: str, drone_name: Optional[str] = None) -> Drone:
        """Get existing drone or create new one"""
        drone = self.db.query(Drone).filter(Drone.drone_id == drone_id).first()
        
        if not drone:
            drone = Drone(
                drone_id=drone_id,
                name=drone_name or f"Drone {drone_id}"
            )
            self.db.add(drone)
            self.db.flush()
            logger.info(f"Created new drone: {drone_id}")
        elif drone_name and drone.name != drone_name:
            drone.name = drone_name
            self.db.flush()
        
        return drone
    
    def get_flight_by_id(self, flight_id: int) -> Optional[Flight]:
        """Get flight by ID with telemetry summary"""
        return self.db.query(Flight).filter(Flight.id == flight_id).first()
    
    def get_flights_by_drone(self, drone_id: int, limit: int = 100) -> list:
        """Get recent flights for a drone"""
        return (
            self.db.query(Flight)
            .filter(Flight.drone_id == drone_id)
            .order_by(Flight.flight_date.desc())
            .limit(limit)
            .all()
        )
