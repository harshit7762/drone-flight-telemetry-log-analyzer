"""
Telemetry Parser using pymavlink to extract high-frequency time-series data
from binary telemetry files (.bin or .tlog).

.bin  → ArduPilot DataFlash binary log (logged on SD card on the FC)
        Message types: RCOU, BAT/BATT, CURR, IMU/IMT, VIBE, GPS, BARO, etc.

.tlog → MAVLink telemetry log (recorded by GCS like Mission Planner)
        Message types: SERVO_OUTPUT_RAW, BATTERY_STATUS, SYS_STATUS,
                       RAW_IMU, SCALED_IMU, GLOBAL_POSITION_INT, etc.
"""
import os
import numpy as np
from typing import Dict, List, Optional
from pymavlink import mavutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelemetryParser:
    """Parse drone telemetry files (.bin or .tlog) and extract metrics"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_ext = os.path.splitext(file_path)[1].lower()
        self.mav_connection = None
        self.messages_count = 0
        self.format_kind = 'tlog' if self.file_ext == '.tlog' else 'bin' if self.file_ext == '.bin' else 'unknown'

        # Data containers (shared between formats)
        self.motor_outputs = {1: [], 2: [], 3: [], 4: []}
        self.battery_data = {
            'voltage': [],
            'current': [],
            'remaining': [],
            'cell_voltages': [],
            'internal_resistance': []
        }
        # Synchronized (voltage_V, current_A) samples for dynamic IR estimation
        self.battery_vi_samples: List[tuple] = []
        self.imu_data = {
            'accel_x': [],
            'accel_y': [],
            'accel_z': []
        }
        self.gps_data = {
            'altitude': [],
            'speed': []
        }
        # GPS fix tracking: list of booleans (True = valid fix at that reading)
        self.gps_fix_data: List[bool] = []
        # Raw temperature readings (for spike detection)
        self.temperature_readings: List[float] = []
        self.temperature_data = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> Dict:
        """
        Parse telemetry file and return aggregated statistics dict.
        Automatically dispatches to the correct handler based on file type.
        """
        try:
            logger.info(f"Parsing file: {self.file_path}  (type={self.file_ext})")

            self.mav_connection = mavutil.mavlink_connection(self.file_path)

            # Determine the actual log format before reading all messages.
            # Some generated files are named .bin but are still MAVLink streams,
            # so extension alone is not reliable.
            detected_kind = None
            for _ in range(30):
                msg = self.mav_connection.recv_match(blocking=False)
                if msg is None:
                    break
                msg_type = msg.get_type()
                if msg_type in ('SERVO_OUTPUT_RAW', 'RCOU', 'BATTERY_STATUS', 'SYS_STATUS', 'RAW_IMU', 'GLOBAL_POSITION_INT', 'SCALED_PRESSURE'):
                    detected_kind = 'tlog'
                    break
                if msg_type in ('RCOU', 'BAT', 'BATT', 'CURR', 'IMU', 'GPS', 'BARO', 'VIBE', 'NKF1', 'XKF1'):
                    detected_kind = 'bin'
                    break
                # Keep scanning for a stable signal.
            if detected_kind is not None:
                self.format_kind = detected_kind
            elif self.file_ext in ('.tlog', '.bin'):
                self.format_kind = self.file_ext[1:]

            # Rewind to the beginning to parse all messages again.
            self.mav_connection.close()
            self.mav_connection = mavutil.mavlink_connection(self.file_path)

            flight_start_time = None
            flight_end_time = None
            seen_msg_types = set()

            while True:
                msg = self.mav_connection.recv_match(blocking=False)
                if msg is None:
                    break

                self.messages_count += 1
                msg_type = msg.get_type()
                seen_msg_types.add(msg_type)

                # Timestamps (present in both formats)
                if hasattr(msg, '_timestamp') and msg._timestamp is not None:
                    ts = msg._timestamp
                    if flight_start_time is None:
                        flight_start_time = ts
                    flight_end_time = ts

                # Route to format-specific handlers
                if self.format_kind == 'bin':
                    self._handle_bin_message(msg_type, msg)
                else:
                    self._handle_tlog_message(msg_type, msg)

            logger.info(f"Detected format: {self.format_kind}")
            logger.info(f"Message types seen: {sorted(seen_msg_types)}")
            logger.info(f"Motor readings   : M1={len(self.motor_outputs[1])}  M2={len(self.motor_outputs[2])}  "
                        f"M3={len(self.motor_outputs[3])}  M4={len(self.motor_outputs[4])}")
            logger.info(f"Battery voltage  : {len(self.battery_data['voltage'])} readings")
            logger.info(f"Battery current  : {len(self.battery_data['current'])} readings")
            logger.info(f"IMU accel_x      : {len(self.imu_data['accel_x'])} readings")
            if self.battery_data['voltage']:
                logger.info(f"Voltage range    : {min(self.battery_data['voltage']):.2f}V – "
                            f"{max(self.battery_data['voltage']):.2f}V")

            duration_seconds = None
            if flight_start_time is not None and flight_end_time is not None:
                duration_seconds = flight_end_time - flight_start_time

            stats = self._calculate_statistics()
            stats['flight_start_time'] = flight_start_time
            stats['flight_end_time'] = flight_end_time
            stats['duration_seconds'] = duration_seconds
            stats['total_messages'] = self.messages_count

            logger.info(f"Parsing complete. {self.messages_count} messages processed.")
            return stats

        except Exception as e:
            logger.error(f"Error parsing telemetry file: {str(e)}")
            raise
        finally:
            if self.mav_connection:
                self.mav_connection.close()

    # ------------------------------------------------------------------
    # .bin  — ArduPilot DataFlash message handlers
    # ------------------------------------------------------------------

    def _handle_bin_message(self, msg_type: str, msg):
        """Dispatch DataFlash (.bin) message types"""

        # ── Motors ──────────────────────────────────────────────────────
        # RCOU: RC Output channels (1-indexed PWM µs values)
        if msg_type == 'RCOU':
            self._bin_extract_rcou(msg)

        # ── Battery ─────────────────────────────────────────────────────
        # BAT / BATT: Battery monitor (ArduPilot 3.6+)
        #   Fields: Volt (V), VoltR (V resting), Curr (A), CurrTot (mAh), Res (%), Temp (C)
        elif msg_type in ('BAT', 'BATT'):
            self._bin_extract_bat(msg)

        # CURR: Older ArduPilot battery message
        #   Fields: Throttle, Volt (mV), Curr (cA), Vcc (mV), CurrTot (mAh), Res (%)
        elif msg_type == 'CURR':
            self._bin_extract_curr(msg)

        # ── IMU / Vibration ─────────────────────────────────────────────
        # IMU / IMT: Raw IMU data
        #   Fields: GyrX,GyrY,GyrZ (rad/s), AccX,AccY,AccZ (m/s²)
        elif msg_type in ('IMU', 'IMT', 'IMU2', 'IMT2'):
            self._bin_extract_imu(msg)

        # VIBE: ArduPilot vibration log (pre-computed)
        #   Fields: VibeX, VibeY, VibeZ (m/s²), Clip0, Clip1, Clip2
        elif msg_type == 'VIBE':
            self._bin_extract_vibe(msg)

        # ── GPS / Altitude ───────────────────────────────────────────────
        # GPS: ArduPilot GPS log
        #   Fields: Status, GMS, GWk, NSats, HDop, Lat, Lng, Alt (m MSL),
        #           Spd (m/s), GCrs, VZ, U
        elif msg_type == 'GPS':
            self._bin_extract_gps(msg)

        # NKF1 / XKF1: EKF position (has RelAlt)
        elif msg_type in ('NKF1', 'XKF1'):
            self._bin_extract_ekf_alt(msg)

        # ── Temperature / Baro ──────────────────────────────────────────
        # BARO: Barometer
        #   Fields: Alt (m), Press (Pa), Temp (C), CRt (m/s)
        elif msg_type == 'BARO':
            self._bin_extract_baro(msg)

    # --- .bin motor ---

    def _bin_extract_rcou(self, msg):
        """RCOU: C1..C14 are PWM outputs in µs.
        1000 µs is the standard ArduPilot disarmed/idle value — exclude it
        so ground-only (never-armed) logs don't produce misleading averages.
        Armed/spinning motors output > 1050 µs.
        """
        for ch, motor_num in [(1, 1), (2, 2), (3, 3), (4, 4)]:
            val = getattr(msg, f'C{ch}', None)
            if val is not None and 1050 < val < 2200:   # armed PWM range only
                self.motor_outputs[motor_num].append(val)

    # --- .bin battery ---

    def _bin_extract_bat(self, msg):
        """BAT/BATT message — values already in V and A.
        Also extracts internal resistance (Res in Ohms → mΩ) and remaining capacity (RemPct in %).
        """
        volt = getattr(msg, 'Volt', None)
        if volt is not None and 1.0 < volt < 100.0:
            self.battery_data['voltage'].append(float(volt))

        curr = getattr(msg, 'Curr', None)
        if curr is not None and curr >= 0:
            self.battery_data['current'].append(float(curr))

        # Synchronized V-I pairing for dynamic resistance estimation
        if volt is not None and curr is not None and 1.0 < volt < 100.0:
            self.battery_vi_samples.append((float(volt), float(curr)))

        # Autopilot estimated internal resistance in Ohms (convert to mΩ)
        res = getattr(msg, 'Res', None)
        if res is not None and 0.00005 <= res <= 5.0:
            self.battery_data['internal_resistance'].append(float(res) * 1000.0)

        # Remaining capacity percentage
        rem_pct = getattr(msg, 'RemPct', None)
        if rem_pct is not None and 0 <= rem_pct <= 100:
            self.battery_data['remaining'].append(float(rem_pct))

    def _bin_extract_curr(self, msg):
        """CURR message — Volt in mV, Curr in centiamps (1/100 A)"""
        v = None
        c = None
        volt = getattr(msg, 'Volt', None)
        if volt is not None and volt > 0:
            v = volt / 1000.0   # mV → V
            if 1.0 < v < 100.0:
                self.battery_data['voltage'].append(v)

        curr = getattr(msg, 'Curr', None)
        if curr is not None and curr > 0:
            c = curr / 100.0   # cA → A
            self.battery_data['current'].append(c)

        if v is not None and c is not None:
            self.battery_vi_samples.append((v, c))

        # Check RemPct or remaining if logged
        rem_pct = getattr(msg, 'RemPct', None)
        if rem_pct is not None and 0 <= rem_pct <= 100:
            self.battery_data['remaining'].append(float(rem_pct))

    # --- .bin IMU ---

    def _bin_extract_imu(self, msg):
        """IMU/IMT: AccX/AccY/AccZ in m/s² (already scaled)"""
        ax = getattr(msg, 'AccX', None)
        ay = getattr(msg, 'AccY', None)
        az = getattr(msg, 'AccZ', None)
        if ax is not None:
            self.imu_data['accel_x'].append(ax)
        if ay is not None:
            self.imu_data['accel_y'].append(ay)
        if az is not None:
            self.imu_data['accel_z'].append(az)

    def _bin_extract_vibe(self, msg):
        """VIBE: VibeX/VibeY/VibeZ are pre-computed vibration in m/s²"""
        vx = getattr(msg, 'VibeX', None)
        vy = getattr(msg, 'VibeY', None)
        vz = getattr(msg, 'VibeZ', None)
        # Only use VIBE if we have no raw IMU data (avoid double-counting)
        if not self.imu_data['accel_x']:
            if vx is not None:
                self.imu_data['accel_x'].append(vx)
            if vy is not None:
                self.imu_data['accel_y'].append(vy)
            if vz is not None:
                self.imu_data['accel_z'].append(vz)

    # --- .bin GPS / altitude ---

    def _bin_extract_gps(self, msg):
        """GPS: Alt in metres MSL, Spd in m/s, Status = fix type (0=no fix, 3=3D)"""
        status = getattr(msg, 'Status', None)
        has_fix = status is not None and status >= 3   # 3 = 3D fix
        self.gps_fix_data.append(has_fix)

        alt = getattr(msg, 'Alt', None)
        if alt is not None and has_fix and alt > -1000:
            self.gps_data['altitude'].append(float(alt))

        spd = getattr(msg, 'Spd', None)
        if spd is not None and has_fix and spd >= 0:
            self.gps_data['speed'].append(float(spd))

    def _bin_extract_ekf_alt(self, msg):
        """NKF1/XKF1: PD field is relative altitude (down=positive, so negate)"""
        pd = getattr(msg, 'PD', None)
        if pd is not None:
            self.gps_data['altitude'].append(float(-pd))   # down → up

    # --- .bin temperature ---

    def _bin_extract_baro(self, msg):
        """BARO: Temp field in degrees Celsius"""
        temp = getattr(msg, 'Temp', None)
        if temp is not None and -50 < temp < 100:
            self.temperature_data.append(float(temp))
            self.temperature_readings.append(float(temp))

    # ------------------------------------------------------------------
    # .tlog — MAVLink telemetry message handlers
    # ------------------------------------------------------------------

    def _handle_tlog_message(self, msg_type: str, msg):
        """Dispatch MAVLink (.tlog) message types"""

        # ── Motors ──────────────────────────────────────────────────────
        if msg_type == 'SERVO_OUTPUT_RAW':
            self._tlog_extract_servo(msg)
        elif msg_type == 'RCOU':
            self._tlog_extract_rcou(msg)

        # ── Battery (all fire independently — a .tlog may carry both) ──
        if msg_type == 'BATTERY_STATUS':
            self._tlog_extract_battery_status(msg)
        if msg_type == 'SYS_STATUS':
            self._tlog_extract_sys_status(msg)
        if msg_type == 'POWER_STATUS':
            self._tlog_extract_power_status(msg)

        # ── IMU ─────────────────────────────────────────────────────────
        if msg_type == 'RAW_IMU':
            self._tlog_extract_raw_imu(msg)
        elif msg_type in ('SCALED_IMU', 'SCALED_IMU2'):
            self._tlog_extract_scaled_imu(msg)

        # ── GPS / Altitude ───────────────────────────────────────────────
        if msg_type == 'GLOBAL_POSITION_INT':
            self._tlog_extract_global_position(msg)

        # ── Temperature ─────────────────────────────────────────────────
        if msg_type == 'SCALED_PRESSURE':
            self._tlog_extract_temperature(msg)

    # --- .tlog motor ---

    def _tlog_extract_servo(self, msg):
        """SERVO_OUTPUT_RAW: servo1_raw … servo4_raw in µs.
        Exclude disarmed idle (1000 µs) — only accept armed/spinning values.
        """
        for i in range(1, 5):
            val = getattr(msg, f'servo{i}_raw', None)
            if val is not None and 1050 < val < 2200:   # armed PWM range only
                self.motor_outputs[i].append(val)

    def _tlog_extract_rcou(self, msg):
        """RCOU (MAVLink variant): chan1_raw … chan4_raw in µs.
        Exclude disarmed idle (1000 µs) — only accept armed/spinning values.
        """
        for ch, motor_num in [(1, 1), (2, 2), (3, 3), (4, 4)]:
            val = getattr(msg, f'chan{ch}_raw', None)
            if val is not None and 1050 < val < 2200:   # armed PWM range only
                self.motor_outputs[motor_num].append(val)

    # --- .tlog battery ---

    def _tlog_extract_battery_status(self, msg):
        """BATTERY_STATUS: voltages[] array in mV (cell-level), current_battery in 10mA"""
        MAVLINK_VOLTAGE_SENTINEL = 65535
        total_volt = None
        curr_val = None
        if hasattr(msg, 'voltages'):
            cells = [v / 1000.0 for v in msg.voltages if 0 < v < MAVLINK_VOLTAGE_SENTINEL]
            if cells:
                total = sum(cells)
                if 1.0 < total < 100.0:
                    self.battery_data['voltage'].append(total)
                    self.battery_data['cell_voltages'].append(cells)
                    total_volt = total

        if hasattr(msg, 'current_battery') and msg.current_battery > 0:
            curr_val = msg.current_battery / 100.0  # 10mA → A
            self.battery_data['current'].append(curr_val)

        if total_volt is not None and curr_val is not None:
            self.battery_vi_samples.append((total_volt, curr_val))

        if hasattr(msg, 'battery_remaining') and msg.battery_remaining >= 0:
            self.battery_data['remaining'].append(msg.battery_remaining)

    def _tlog_extract_sys_status(self, msg):
        """SYS_STATUS: voltage_battery in mV, current_battery in 10mA"""
        v = None
        c = None
        if hasattr(msg, 'voltage_battery') and msg.voltage_battery > 0:
            v = msg.voltage_battery / 1000.0
            if 1.0 < v < 100.0:
                self.battery_data['voltage'].append(v)

        if hasattr(msg, 'current_battery') and msg.current_battery > 0:
            c = msg.current_battery / 100.0
            self.battery_data['current'].append(c)

        if v is not None and c is not None:
            self.battery_vi_samples.append((v, c))

        if hasattr(msg, 'battery_remaining') and msg.battery_remaining >= 0:
            self.battery_data['remaining'].append(msg.battery_remaining)

    def _tlog_extract_power_status(self, msg):
        """POWER_STATUS: Vcc is 5V rail in mV — only use as last-resort fallback"""
        if not self.battery_data['voltage']:
            vcc = getattr(msg, 'Vcc', None)
            if vcc and vcc > 0:
                v = vcc / 1000.0
                if 1.0 < v < 100.0:
                    self.battery_data['voltage'].append(v)

    # --- .tlog IMU ---

    def _tlog_extract_raw_imu(self, msg):
        """RAW_IMU: xacc/yacc/zacc in milli-g (1/1000 g).
        Normalized to m/s² so that .bin and .tlog vibration metrics share the same unit.
        """
        G = 9.80665
        if hasattr(msg, 'xacc') and msg.xacc is not None:
            self.imu_data['accel_x'].append(float(msg.xacc) * G / 1000.0)
        if hasattr(msg, 'yacc') and msg.yacc is not None:
            self.imu_data['accel_y'].append(float(msg.yacc) * G / 1000.0)
        if hasattr(msg, 'zacc') and msg.zacc is not None:
            self.imu_data['accel_z'].append(float(msg.zacc) * G / 1000.0)

    def _tlog_extract_scaled_imu(self, msg):
        """SCALED_IMU / SCALED_IMU2: xacc/yacc/zacc in milli-g.
        Normalized to m/s².
        """
        G = 9.80665
        if hasattr(msg, 'xacc') and msg.xacc is not None:
            self.imu_data['accel_x'].append(float(msg.xacc) * G / 1000.0)
        if hasattr(msg, 'yacc') and msg.yacc is not None:
            self.imu_data['accel_y'].append(float(msg.yacc) * G / 1000.0)
        if hasattr(msg, 'zacc') and msg.zacc is not None:
            self.imu_data['accel_z'].append(float(msg.zacc) * G / 1000.0)

    # --- .tlog GPS / altitude ---

    def _tlog_extract_global_position(self, msg):
        """GLOBAL_POSITION_INT: relative_alt in mm, vx/vy in cm/s.
        This message is only sent when the GCS receives valid position data,
        so its presence implies a GPS fix. We mark each reading as a fix.
        """
        self.gps_fix_data.append(True)   # message presence = fix

        if hasattr(msg, 'relative_alt'):
            alt = msg.relative_alt / 1000.0   # mm → m
            if alt > -100:                     # filter pre-arm garbage
                self.gps_data['altitude'].append(alt)

        if hasattr(msg, 'vx') and hasattr(msg, 'vy'):
            speed = np.sqrt((msg.vx / 100.0) ** 2 + (msg.vy / 100.0) ** 2)
            self.gps_data['speed'].append(speed)

    # --- .tlog temperature ---

    def _tlog_extract_temperature(self, msg):
        """SCALED_PRESSURE: temperature in cdegC (1/100 °C)"""
        if hasattr(msg, 'temperature'):
            temp = msg.temperature / 100.0
            if -50 < temp < 100:
                self.temperature_data.append(temp)
                self.temperature_readings.append(temp)

    def _estimate_dynamic_internal_resistance(self) -> Optional[float]:
        """
        Dynamically estimate battery internal resistance (in mΩ) from synchronized
        voltage and current steps during active flight (ΔV / ΔI method).
        Used when autopilot-logged internal resistance (BAT.Res) is not available.
        """
        if len(self.battery_vi_samples) < 15:
            return None

        v_arr = np.array([s[0] for s in self.battery_vi_samples])
        i_arr = np.array([s[1] for s in self.battery_vi_samples])

        # Filter to active flight (current >= 2.0A)
        active = i_arr >= 2.0
        v_active = v_arr[active]
        i_active = i_arr[active]

        if len(i_active) < 10:
            return None

        # 1. Delta method on consecutive active samples
        dv = np.diff(v_active)
        di = np.diff(i_active)

        # Significant throttle/current step changes (>= 1.5A)
        step_mask = np.abs(di) >= 1.5
        if np.sum(step_mask) >= 3:
            r_samples = -dv[step_mask] / di[step_mask]
            # Physically realistic drone LiPo pack resistance: 0.5 mΩ to 300 mΩ (0.0005 to 0.300 Ohm)
            valid = r_samples[(r_samples >= 0.0005) & (r_samples <= 0.300)]
            if len(valid) >= 2:
                return float(np.median(valid) * 1000.0)

        # 2. Linear regression slope fallback if current span is wide (>= 5A)
        if (np.max(i_active) - np.min(i_active)) >= 5.0 and len(i_active) >= 20:
            cov = np.cov(i_active, v_active)[0, 1]
            var_i = np.var(i_active)
            if var_i > 1e-4:
                slope = cov / var_i  # dV/dI = -R_int
                r_est = -slope
                if 0.0005 <= r_est <= 0.300:
                    return float(r_est * 1000.0)

        return None

    # ------------------------------------------------------------------
    # Statistics calculation (format-agnostic)
    # ------------------------------------------------------------------

    def _calculate_statistics(self) -> Dict:
        """Calculate avg/max statistics for all collected metrics"""
        stats = {}

        # Motors
        # Only readings > 1050 µs (armed/spinning) are stored; disarmed idle
        # (1000 µs) is excluded at collection time.  If no motor ever exceeded
        # the armed threshold the flight is flagged as ground-only below.
        motors_have_data = False
        for motor_num in range(1, 5):
            data = self.motor_outputs[motor_num]
            if data:
                stats[f'motor{motor_num}_avg'] = float(np.mean(data))
                stats[f'motor{motor_num}_max'] = float(np.max(data))
                motors_have_data = True
            else:
                stats[f'motor{motor_num}_avg'] = None
                stats[f'motor{motor_num}_max'] = None

        # Ground-only detection: no motor ever reached armed PWM threshold.
        # Causes: drone was never armed, a very short pre-arm Replay log, or
        # the log file contains only ground/bench data.
        stats['is_ground_only'] = not motors_have_data

        # Battery voltage
        if self.battery_data['voltage']:
            stats['battery_voltage_avg'] = float(np.mean(self.battery_data['voltage']))
            stats['battery_voltage_min'] = float(np.min(self.battery_data['voltage']))
        else:
            stats['battery_voltage_avg'] = None
            stats['battery_voltage_min'] = None

        # Battery current
        if self.battery_data['current']:
            stats['battery_current_avg'] = float(np.mean(self.battery_data['current']))
            stats['battery_current_max'] = float(np.max(self.battery_data['current']))
        else:
            stats['battery_current_avg'] = None
            stats['battery_current_max'] = None

        # Battery remaining %
        if self.battery_data['remaining']:
            stats['battery_remaining_avg'] = float(np.mean(self.battery_data['remaining']))
        else:
            stats['battery_remaining_avg'] = None

        # Cell voltages
        if self.battery_data['cell_voltages']:
            all_cells = [v for reading in self.battery_data['cell_voltages'] for v in reading]
            stats['cell_voltages'] = {
                'avg': float(np.mean(all_cells)),
                'min': float(np.min(all_cells)),
                'max': float(np.max(all_cells))
            }
        else:
            stats['cell_voltages'] = None

        # Battery Internal Resistance (in mΩ)
        # 1. From autopilot direct logging (BAT.Res in .bin)
        if self.battery_data['internal_resistance']:
            stats['battery_internal_resistance_avg'] = float(np.mean(self.battery_data['internal_resistance']))
            stats['battery_internal_resistance_min'] = float(np.min(self.battery_data['internal_resistance']))
            stats['battery_internal_resistance_max'] = float(np.max(self.battery_data['internal_resistance']))
        else:
            # 2. Dynamic estimation from V-I delta under load
            dyn_ir = self._estimate_dynamic_internal_resistance()
            if dyn_ir is not None:
                stats['battery_internal_resistance_avg'] = dyn_ir
                stats['battery_internal_resistance_min'] = dyn_ir
                stats['battery_internal_resistance_max'] = dyn_ir
            else:
                stats['battery_internal_resistance_avg'] = None
                stats['battery_internal_resistance_min'] = None
                stats['battery_internal_resistance_max'] = None

        # IMU / Vibration
        for axis in ('x', 'y', 'z'):
            data = self.imu_data[f'accel_{axis}']
            if data:
                abs_data = np.abs(data)
                stats[f'vibration_{axis}_avg'] = float(np.mean(abs_data))
                stats[f'vibration_{axis}_max'] = float(np.max(abs_data))
            else:
                stats[f'vibration_{axis}_avg'] = None
                stats[f'vibration_{axis}_max'] = None

        # Vibration magnitude
        if all(self.imu_data[f'accel_{a}'] for a in ('x', 'y', 'z')):
            ax = np.array(self.imu_data['accel_x'])
            ay = np.array(self.imu_data['accel_y'])
            az = np.array(self.imu_data['accel_z'])
            magnitudes = np.sqrt(ax**2 + ay**2 + az**2)
            stats['vibration_magnitude_avg'] = float(np.mean(magnitudes))
            stats['vibration_magnitude_max'] = float(np.max(magnitudes))
        else:
            stats['vibration_magnitude_avg'] = None
            stats['vibration_magnitude_max'] = None

        # GPS / Altitude
        if self.gps_data['altitude']:
            stats['altitude_avg'] = float(np.mean(self.gps_data['altitude']))
            stats['altitude_max'] = float(np.max(self.gps_data['altitude']))
        else:
            stats['altitude_avg'] = None
            stats['altitude_max'] = None

        if self.gps_data['speed']:
            stats['speed_avg'] = float(np.mean(self.gps_data['speed']))
            stats['speed_max'] = float(np.max(self.gps_data['speed']))
        else:
            stats['speed_avg'] = None
            stats['speed_max'] = None

        # GPS fix quality
        if self.gps_fix_data:
            fix_count = sum(self.gps_fix_data)
            total = len(self.gps_fix_data)
            stats['gps_fix_count'] = fix_count
            stats['total_gps_messages'] = total
            stats['gps_fix_ratio'] = fix_count / total if total > 0 else None
        else:
            stats['gps_fix_count'] = None
            stats['total_gps_messages'] = None
            stats['gps_fix_ratio'] = None

        # Temperature
        if self.temperature_data:
            stats['temperature_avg'] = float(np.mean(self.temperature_data))
            stats['temperature_max'] = float(np.max(self.temperature_data))
        else:
            stats['temperature_avg'] = None
            stats['temperature_max'] = None

        # Temperature spike count (readings > avg + 2 standard deviations)
        if self.temperature_readings and len(self.temperature_readings) >= 5:
            arr = np.array(self.temperature_readings)
            spike_threshold = float(np.mean(arr) + 2 * np.std(arr))
            stats['temperature_spike_count'] = int(np.sum(arr > spike_threshold))
        else:
            stats['temperature_spike_count'] = None

        return stats


def parse_telemetry_file(file_path: str) -> Dict:
    """
    Convenience function to parse a telemetry file.

    Args:
        file_path: Path to the .bin or .tlog file

    Returns:
        Dictionary of aggregated statistics
    """
    parser = TelemetryParser(file_path)
    return parser.parse()
