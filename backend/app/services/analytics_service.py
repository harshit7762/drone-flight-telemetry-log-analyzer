"""
Analytics Service for Predictive Maintenance
Implements rolling-average comparison algorithm to detect component wear
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime
from app.models import Drone, Flight, TelemetrySummary, MaintenanceAlert
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsService:
    """Service for predictive maintenance analytics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = settings
    
    def analyze_flight_and_generate_alerts(self, flight_id: int) -> List[MaintenanceAlert]:
        """
        Analyze a flight and generate predictive maintenance alerts
        
        Args:
            flight_id: ID of the flight to analyze
        
        Returns:
            List of generated maintenance alerts
        """
        alerts = []
        
        try:
            # Get current flight with telemetry
            flight = self.db.query(Flight).filter(Flight.id == flight_id).first()
            if not flight or not flight.telemetry_summary:
                logger.warning(f"Flight {flight_id} not found or has no telemetry data")
                return alerts
            
            current_telemetry = flight.telemetry_summary
            
            # Get historical baseline (rolling window of previous flights)
            historical_flights = self._get_historical_flights(
                flight.drone_id,
                flight_id,
                window_size=self.settings.ROLLING_WINDOW_FLIGHTS
            )
            
            if len(historical_flights) < 2:
                logger.info(f"Not enough historical data for drone {flight.drone_id} (need at least 2 previous flights)")
                return alerts
            
            # Calculate baselines from historical data
            baselines = self._calculate_baselines(historical_flights)
            
            # Analyze motor outputs
            motor_alerts = self._analyze_motors(
                current_telemetry, baselines, flight.drone_id, flight_id
            )
            alerts.extend(motor_alerts)

            # Analyze battery metrics
            battery_alerts = self._analyze_battery(
                current_telemetry, baselines, flight.drone_id, flight_id
            )
            alerts.extend(battery_alerts)

            # Analyze vibration metrics
            vibration_alerts = self._analyze_vibrations(
                current_telemetry, baselines, flight.drone_id, flight_id
            )
            alerts.extend(vibration_alerts)

            # Analyze GPS signal quality
            gps_alerts = self._analyze_gps(
                current_telemetry, baselines, flight.drone_id, flight_id
            )
            alerts.extend(gps_alerts)

            # Analyze temperature
            temperature_alerts = self._analyze_temperature(
                current_telemetry, baselines, flight.drone_id, flight_id
            )
            alerts.extend(temperature_alerts)
            
            # Save all alerts to database
            for alert in alerts:
                self.db.add(alert)
            self.db.commit()
            
            logger.info(f"Generated {len(alerts)} alerts for flight {flight_id}")
            
        except Exception as e:
            logger.error(f"Error analyzing flight {flight_id}: {str(e)}")
            self.db.rollback()
            raise
        
        return alerts
    
    def _get_historical_flights(
        self,
        drone_id: int,
        current_flight_id: int,
        window_size: int
    ) -> List[Flight]:
        """Get historical flights for baseline calculation"""
        return (
            self.db.query(Flight)
            .filter(
                Flight.drone_id == drone_id,
                Flight.id < current_flight_id
            )
            .order_by(desc(Flight.flight_date))
            .limit(window_size)
            .all()
        )
    
    def _calculate_baselines(self, historical_flights: List[Flight]) -> Dict:
        """Calculate baseline averages from historical flight data"""
        baselines = {}

        metrics = {
            'motor1_avg': [], 'motor1_max': [],
            'motor2_avg': [], 'motor2_max': [],
            'motor3_avg': [], 'motor3_max': [],
            'motor4_avg': [], 'motor4_max': [],
            'battery_voltage_avg': [], 'battery_voltage_min': [],
            'battery_current_avg': [], 'battery_current_max': [],
            'battery_internal_resistance_avg': [],
            'vibration_x_avg': [], 'vibration_x_max': [],
            'vibration_y_avg': [], 'vibration_y_max': [],
            'vibration_z_avg': [], 'vibration_z_max': [],
            'vibration_magnitude_avg': [], 'vibration_magnitude_max': [],
            # New
            'gps_fix_ratio': [],
            'temperature_avg': [], 'temperature_max': [],
            'temperature_spike_count': [],
        }

        for flight in historical_flights:
            if flight.telemetry_summary:
                ts = flight.telemetry_summary
                for key in metrics.keys():
                    value = getattr(ts, key, None)
                    if value is not None:
                        metrics[key].append(value)

        for key, values in metrics.items():
            baselines[key] = float(np.mean(values)) if values else None

        return baselines
    
    def _analyze_motors(
        self,
        current: TelemetrySummary,
        baselines: Dict,
        drone_id: int,
        flight_id: int
    ) -> List[MaintenanceAlert]:
        """Analyze motor PWM outputs for anomalies"""
        alerts = []
        threshold = self.settings.MOTOR_PWM_THRESHOLD_PERCENT

        for motor_num in range(1, 5):
            # Check average PWM
            current_avg = getattr(current, f'motor{motor_num}_avg', None)
            baseline_avg = baselines.get(f'motor{motor_num}_avg')

            # Use 'is not None' — a value of 0 is falsy but still valid
            if current_avg is not None and baseline_avg is not None:
                deviation = self._calculate_deviation_percent(current_avg, baseline_avg)
                if abs(deviation) > threshold:
                    severity = self._determine_severity(abs(deviation), threshold)
                    alerts.append(MaintenanceAlert(
                        drone_id=drone_id,
                        flight_id=flight_id,
                        alert_type="motor",
                        component=f"motor_{motor_num}",
                        severity=severity,
                        metric_name=f"motor{motor_num}_avg_pwm",
                        current_value=current_avg,
                        baseline_value=baseline_avg,
                        deviation_percent=deviation,
                        threshold_percent=threshold,
                        message=self._generate_motor_message(motor_num, deviation, current_avg, baseline_avg),
                        recommendation=self._generate_motor_recommendation(motor_num, deviation)
                    ))

            # Check maximum PWM
            current_max = getattr(current, f'motor{motor_num}_max', None)
            baseline_max = baselines.get(f'motor{motor_num}_max')

            if current_max is not None and baseline_max is not None:
                deviation = self._calculate_deviation_percent(current_max, baseline_max)
                if abs(deviation) > threshold:
                    severity = self._determine_severity(abs(deviation), threshold)
                    alerts.append(MaintenanceAlert(
                        drone_id=drone_id,
                        flight_id=flight_id,
                        alert_type="motor",
                        component=f"motor_{motor_num}",
                        severity=severity,
                        metric_name=f"motor{motor_num}_max_pwm",
                        current_value=current_max,
                        baseline_value=baseline_max,
                        deviation_percent=deviation,
                        threshold_percent=threshold,
                        message=f"Motor {motor_num} max PWM deviated {deviation:.1f}% from baseline ({baseline_max:.0f} → {current_max:.0f} μs)",
                        recommendation=self._generate_motor_recommendation(motor_num, deviation)
                    ))

        return alerts
    
    def _analyze_battery(
        self,
        current: TelemetrySummary,
        baselines: Dict,
        drone_id: int,
        flight_id: int
    ) -> List[MaintenanceAlert]:
        """Analyze battery metrics for degradation"""
        alerts = []
        threshold = self.settings.BATTERY_VOLTAGE_THRESHOLD_PERCENT

        # Check average voltage
        if current.battery_voltage_avg is not None and baselines.get('battery_voltage_avg') is not None:
            deviation = self._calculate_deviation_percent(
                current.battery_voltage_avg, baselines['battery_voltage_avg']
            )
            if deviation < -threshold:   # only alert on voltage DROP
                severity = self._determine_severity(abs(deviation), threshold)
                alerts.append(MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="battery",
                    component="battery",
                    severity=severity,
                    metric_name="battery_voltage_avg",
                    current_value=current.battery_voltage_avg,
                    baseline_value=baselines['battery_voltage_avg'],
                    deviation_percent=deviation,
                    threshold_percent=threshold,
                    message=f"Battery avg voltage dropped {abs(deviation):.1f}% below baseline "
                            f"({baselines['battery_voltage_avg']:.2f}V → {current.battery_voltage_avg:.2f}V)",
                    recommendation="Inspect battery for damage, check cell balance, consider "
                                   "replacement if degradation continues across flights."
                ))

        # Check minimum voltage
        if current.battery_voltage_min is not None and baselines.get('battery_voltage_min') is not None:
            deviation = self._calculate_deviation_percent(
                current.battery_voltage_min, baselines['battery_voltage_min']
            )
            if deviation < -threshold:
                severity = self._determine_severity(abs(deviation), threshold)
                alerts.append(MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="battery",
                    component="battery",
                    severity=severity,
                    metric_name="battery_voltage_min",
                    current_value=current.battery_voltage_min,
                    baseline_value=baselines['battery_voltage_min'],
                    deviation_percent=deviation,
                    threshold_percent=threshold,
                    message=f"Battery minimum voltage dropped {abs(deviation):.1f}% below baseline "
                            f"({baselines['battery_voltage_min']:.2f}V → {current.battery_voltage_min:.2f}V)",
                    recommendation="Battery may be reaching end of life. Check cell voltages "
                                   "individually and plan for replacement."
                ))

        # Check internal resistance (mΩ)
        ir_curr = current.battery_internal_resistance_avg
        ir_baseline = baselines.get('battery_internal_resistance_avg')
        ir_threshold = getattr(self.settings, 'BATTERY_RESISTANCE_THRESHOLD_PERCENT', 25.0)
        ir_max_abs = getattr(self.settings, 'BATTERY_RESISTANCE_MAX_ABSOLUTE_MOHM', 60.0)

        # 1. Relative increase vs baseline
        if ir_curr is not None and ir_baseline is not None and ir_baseline > 0:
            deviation = self._calculate_deviation_percent(ir_curr, ir_baseline)
            if deviation > ir_threshold:  # Only alert on resistance INCREASE
                severity = self._determine_severity(deviation, ir_threshold)
                alerts.append(MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="battery",
                    component="battery",
                    severity=severity,
                    metric_name="battery_internal_resistance_avg",
                    current_value=round(ir_curr, 2),
                    baseline_value=round(ir_baseline, 2),
                    deviation_percent=round(deviation, 2),
                    threshold_percent=ir_threshold,
                    message=f"Battery internal resistance increased {deviation:.1f}% above baseline "
                            f"({ir_baseline:.1f} mΩ → {ir_curr:.1f} mΩ)",
                    recommendation="Higher internal resistance indicates cell aging or degradation, causing "
                                   "voltage sag under throttle and excess heating. Test individual cell resistances "
                                   "with a balance charger and consider retiring this pack from high-load missions."
                ))

        # 2. Absolute threshold check (regardless of baseline)
        if ir_curr is not None and ir_curr > ir_max_abs:
            severity = "critical" if ir_curr >= (ir_max_abs * 1.5) else "warning"
            alerts.append(MaintenanceAlert(
                drone_id=drone_id,
                flight_id=flight_id,
                alert_type="battery",
                component="battery",
                severity=severity,
                metric_name="battery_internal_resistance_max_abs",
                current_value=round(ir_curr, 2),
                baseline_value=ir_max_abs,
                deviation_percent=round(((ir_curr - ir_max_abs) / ir_max_abs) * 100, 2),
                threshold_percent=ir_threshold,
                message=f"Battery internal resistance is critically high ({ir_curr:.1f} mΩ — safe max: {ir_max_abs:.1f} mΩ)",
                recommendation="Excessive pack resistance poses severe risk of in-flight voltage brownout and cutoffs. "
                               "Inspect battery immediately for swelling, heat spots, or cell imbalance, and replace."
            ))

        return alerts
    
    def _analyze_vibrations(
        self,
        current: TelemetrySummary,
        baselines: Dict,
        drone_id: int,
        flight_id: int
    ) -> List[MaintenanceAlert]:
        """Analyze vibration metrics for mechanical issues"""
        alerts = []
        threshold = self.settings.VIBRATION_THRESHOLD_PERCENT
        min_floor = getattr(self.settings, 'VIBRATION_MIN_FLOOR_ABS', 1.0)
        
        # Check overall vibration magnitude (only alert if above noise floor)
        if (
            current.vibration_magnitude_avg is not None 
            and baselines.get('vibration_magnitude_avg') is not None
            and current.vibration_magnitude_avg >= min_floor
        ):
            # Clamp baseline to min_floor to prevent near-zero division explosion
            effective_baseline = max(baselines['vibration_magnitude_avg'], min_floor)
            deviation = self._calculate_deviation_percent(
                current.vibration_magnitude_avg,
                effective_baseline
            )
            
            # Increased vibration indicates mechanical issues
            if deviation > threshold:
                severity = self._determine_severity(abs(deviation), threshold)
                
                alert = MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="vibration",
                    component="imu",
                    severity=severity,
                    metric_name="vibration_magnitude_avg",
                    current_value=current.vibration_magnitude_avg,
                    baseline_value=baselines['vibration_magnitude_avg'],
                    deviation_percent=deviation,
                    threshold_percent=threshold,
                    message=f"Overall vibration has increased {deviation:.1f}% from baseline",
                    recommendation="Check propeller balance, motor mounts, and frame integrity. Unbalanced propellers are a common cause"
                )
                alerts.append(alert)
        
        # Check individual axes for specific issues
        for axis in ['x', 'y', 'z']:
            current_val = getattr(current, f'vibration_{axis}_avg', None)
            baseline_val = baselines.get(f'vibration_{axis}_avg')
            
            if (
                current_val is not None 
                and baseline_val is not None
                and current_val >= min_floor
            ):
                effective_baseline = max(baseline_val, min_floor)
                deviation = self._calculate_deviation_percent(current_val, effective_baseline)
                
                if deviation > threshold:
                    severity = self._determine_severity(abs(deviation), threshold)
                    
                    alert = MaintenanceAlert(
                        drone_id=drone_id,
                        flight_id=flight_id,
                        alert_type="vibration",
                        component=f"imu_{axis}_axis",
                        severity=severity,
                        metric_name=f"vibration_{axis}_avg",
                        current_value=current_val,
                        baseline_value=baseline_val,
                        deviation_percent=deviation,
                        threshold_percent=threshold,
                        message=f"Vibration on {axis.upper()}-axis has increased {deviation:.1f}% from baseline",
                        recommendation=self._generate_vibration_recommendation(axis, deviation)
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _calculate_deviation_percent(self, current: float, baseline: float) -> float:
        """Calculate percentage deviation from baseline"""
        if baseline == 0 or abs(baseline) < 1e-6:
            return 0.0
        return ((current - baseline) / baseline) * 100.0
    
    def _determine_severity(self, deviation: float, threshold: float) -> str:
        """
        Determine alert severity based on how far the deviation exceeds the threshold.

        Bands (as multiples of threshold):
          deviation >= 2.0 × threshold  → critical
          deviation >= 1.5 × threshold  → warning
          deviation >= 1.0 × threshold  → info

        This means:
          Motor  (threshold=15%): info @15%, warning @22.5%, critical @30%
          Battery(threshold=10%): info @10%, warning @15%,   critical @20%
          Vibration(threshold=20%): info @20%, warning @30%, critical @40%
          GPS    (threshold=15%): info @15%, warning @22.5%, critical @30%
        """
        if deviation >= threshold * 2.0:
            return "critical"
        elif deviation >= threshold * 1.5:
            return "warning"
        return "info"
    
    def _generate_motor_message(
        self,
        motor_num: int,
        deviation: float,
        current: float,
        baseline: float
    ) -> str:
        """Generate human-readable message for motor alerts"""
        direction = "increased" if deviation > 0 else "decreased"
        return (
            f"Motor {motor_num} average PWM output has {direction} {abs(deviation):.1f}% "
            f"from baseline ({baseline:.0f} → {current:.0f} μs)"
        )
    
    def _generate_motor_recommendation(self, motor_num: int, deviation: float) -> str:
        """Generate recommendation for motor alerts"""
        if deviation > 0:
            return (
                f"Motor {motor_num} is working harder than normal. "
                "Check for propeller damage, motor bearing wear, or increased resistance. "
                "Inspect ESC connections and motor windings."
            )
        else:
            return (
                f"Motor {motor_num} output is lower than normal. "
                "Check ESC calibration, motor connections, or potential motor failure. "
                "Verify propeller is properly attached."
            )
    
    def _generate_vibration_recommendation(self, axis: str, deviation: float) -> str:
        """Generate recommendation for vibration alerts"""
        axis_map = {
            'x': 'roll axis (side-to-side)',
            'y': 'pitch axis (front-to-back)',
            'z': 'yaw axis (vertical)'
        }
        axis_desc = axis_map.get(axis, axis)

        return (
            f"Increased vibration on {axis_desc}. "
            "Check propeller balance and condition, tighten motor mounts, "
            "inspect frame for cracks, and verify landing gear integrity."
        )

    # ------------------------------------------------------------------
    # GPS Signal Loss Analyzer
    # ------------------------------------------------------------------

    def _analyze_gps(
        self,
        current: TelemetrySummary,
        baselines: Dict,
        drone_id: int,
        flight_id: int
    ) -> List[MaintenanceAlert]:
        """Detect GPS signal degradation or loss events."""
        alerts = []

        fix_ratio = getattr(current, 'gps_fix_ratio', None)
        if fix_ratio is None:
            return alerts   # No GPS data in this file — skip silently

        # ── Absolute check: fix ratio below safe minimum regardless of baseline ──
        abs_min = self.settings.GPS_FIX_RATIO_MIN_ABSOLUTE
        if fix_ratio < abs_min:
            loss_pct = (1.0 - fix_ratio) * 100
            # Express how far below the minimum as a % of the minimum (so severity bands work)
            deviation_from_min_pct = abs(fix_ratio - abs_min) / abs_min * 100
            threshold = self.settings.GPS_FIX_RATIO_THRESHOLD_PERCENT
            severity = self._determine_severity(deviation_from_min_pct, threshold)
            alerts.append(MaintenanceAlert(
                drone_id=drone_id,
                flight_id=flight_id,
                alert_type="gps",
                component="gps",
                severity=severity,
                metric_name="gps_fix_ratio",
                current_value=round(fix_ratio, 4),
                baseline_value=abs_min,
                deviation_percent=round((fix_ratio - abs_min) / abs_min * 100, 2),
                threshold_percent=self.settings.GPS_FIX_RATIO_THRESHOLD_PERCENT,
                message=(
                    f"GPS signal lost {loss_pct:.1f}% of the flight "
                    f"(fix ratio: {fix_ratio*100:.1f}% — minimum safe: {abs_min*100:.0f}%)"
                ),
                recommendation=(
                    "Check GPS antenna for damage or obstruction, verify cable connections, "
                    "move GPS mast away from interference sources (ESCs, power cables), "
                    "and check for electromagnetic interference from other electronics."
                )
            ))

        # ── Relative check: significantly worse than this drone's own baseline ──
        baseline_ratio = baselines.get('gps_fix_ratio')
        if baseline_ratio and fix_ratio < baseline_ratio:
            deviation = self._calculate_deviation_percent(fix_ratio, baseline_ratio)
            threshold = self.settings.GPS_FIX_RATIO_THRESHOLD_PERCENT
            if abs(deviation) > threshold:
                severity = self._determine_severity(abs(deviation), threshold)
                alerts.append(MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="gps",
                    component="gps",
                    severity=severity,
                    metric_name="gps_fix_ratio_vs_baseline",
                    current_value=round(fix_ratio, 4),
                    baseline_value=round(baseline_ratio, 4),
                    deviation_percent=round(deviation, 2),
                    threshold_percent=threshold,
                    message=(
                        f"GPS fix quality degraded {abs(deviation):.1f}% vs baseline "
                        f"({baseline_ratio*100:.1f}% → {fix_ratio*100:.1f}% fix rate)"
                    ),
                    recommendation=(
                        "GPS performance has degraded compared to previous flights. "
                        "Inspect the GPS module and antenna, check for new interference "
                        "sources, and consider a compass/GPS calibration."
                    )
                ))

        return alerts

    # ------------------------------------------------------------------
    # Temperature Spike Analyzer
    # ------------------------------------------------------------------

    def _analyze_temperature(
        self,
        current: TelemetrySummary,
        baselines: Dict,
        drone_id: int,
        flight_id: int
    ) -> List[MaintenanceAlert]:
        """Detect overheating via average temperature rise and spike counts."""
        alerts = []

        temp_avg = getattr(current, 'temperature_avg', None)
        temp_max = getattr(current, 'temperature_max', None)
        spike_count = getattr(current, 'temperature_spike_count', None)

        if temp_avg is None and temp_max is None:
            return alerts   # No temperature data — skip silently

        # ── Absolute max check: exceeds safe operating temperature ──
        abs_max = self.settings.TEMPERATURE_MAX_ABSOLUTE_CELSIUS
        if temp_max is not None and temp_max >= abs_max:
            severity = "critical" if temp_max >= abs_max + 10 else "warning"
            alerts.append(MaintenanceAlert(
                drone_id=drone_id,
                flight_id=flight_id,
                alert_type="temperature",
                component="autopilot",
                severity=severity,
                metric_name="temperature_max",
                current_value=round(temp_max, 1),
                baseline_value=abs_max,
                deviation_percent=round((temp_max - abs_max) / abs_max * 100, 2),
                threshold_percent=0,
                message=(
                    f"Maximum temperature reached {temp_max:.1f}°C, "
                    f"exceeding safe limit of {abs_max:.0f}°C"
                ),
                recommendation=(
                    "Check autopilot/ESC cooling and airflow. Inspect for blocked vents, "
                    "damaged heat sinks, or failing cooling fans. Avoid flying in "
                    "extreme ambient heat without additional cooling measures."
                )
            ))

        # ── Relative check: avg temperature significantly higher than baseline ──
        baseline_temp = baselines.get('temperature_avg')
        threshold_c = self.settings.TEMPERATURE_AVG_THRESHOLD_CELSIUS
        if temp_avg is not None and baseline_temp is not None:
            delta = temp_avg - baseline_temp   # direct Celsius difference
            if delta > threshold_c:
                severity = "critical" if delta >= threshold_c * 2 else "warning"
                alerts.append(MaintenanceAlert(
                    drone_id=drone_id,
                    flight_id=flight_id,
                    alert_type="temperature",
                    component="autopilot",
                    severity=severity,
                    metric_name="temperature_avg",
                    current_value=round(temp_avg, 1),
                    baseline_value=round(baseline_temp, 1),
                    deviation_percent=round(delta / baseline_temp * 100, 2),
                    threshold_percent=threshold_c,
                    message=(
                        f"Average flight temperature is {delta:.1f}°C above baseline "
                        f"({baseline_temp:.1f}°C → {temp_avg:.1f}°C)"
                    ),
                    recommendation=(
                        "Elevated operating temperature detected. Check autopilot enclosure "
                        "ventilation, inspect ESC thermal performance, and verify no "
                        "components are running unusually hot."
                    )
                ))

        # ── Spike count check: too many thermal spikes during flight ──
        spike_threshold = self.settings.TEMPERATURE_SPIKE_COUNT_THRESHOLD
        if spike_count is not None and spike_count >= spike_threshold:
            alerts.append(MaintenanceAlert(
                drone_id=drone_id,
                flight_id=flight_id,
                alert_type="temperature",
                component="autopilot",
                severity="warning",
                metric_name="temperature_spike_count",
                current_value=float(spike_count),
                baseline_value=float(spike_threshold),
                deviation_percent=round((spike_count - spike_threshold) / spike_threshold * 100, 2),
                threshold_percent=float(spike_threshold),
                message=(
                    f"{spike_count} temperature spikes detected during flight "
                    f"(threshold: {spike_threshold} spikes)"
                ),
                recommendation=(
                    "Intermittent thermal spikes suggest a loose connection, "
                    "a failing temperature sensor, or brief overload events on a "
                    "specific component. Check wiring and ESC connections."
                )
            ))

        return alerts
    
    def get_drone_health_summary(self, drone_id: int) -> Dict:
        """Get overall health summary for a drone"""
        # Get recent unresolved alerts
        recent_alerts = (
            self.db.query(MaintenanceAlert)
            .filter(
                MaintenanceAlert.drone_id == drone_id,
                MaintenanceAlert.resolved == False
            )
            .order_by(desc(MaintenanceAlert.created_at))
            .limit(10)
            .all()
        )
        
        # Count alerts by severity
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        for alert in recent_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        # Determine overall health status
        if severity_counts["critical"] > 0:
            health_status = "critical"
        elif severity_counts["warning"] > 0:
            health_status = "warning"
        elif severity_counts["info"] > 0:
            health_status = "attention"
        else:
            health_status = "healthy"
        
        return {
            "drone_id": drone_id,
            "health_status": health_status,
            "alert_counts": severity_counts,
            "total_unresolved_alerts": len(recent_alerts),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "component": alert.component,
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in recent_alerts
            ]
        }
