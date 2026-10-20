import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { flightsAPI } from '../services/api';
import { 
  ArrowLeft, 
  Battery, 
  Gauge, 
  Activity, 
  Thermometer, 
  AlertTriangle, 
  Zap, 
  Navigation, 
  Radio, 
  CheckCircle, 
  AlertCircle, 
  XCircle 
} from 'lucide-react';
import { formatDate, formatDuration, formatNumber } from '../utils/helpers';

function MetricCard({ icon: Icon, label, value, unit, color }) {
  return (
    <div className="card" style={{ borderLeft: `4px solid ${color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <Icon size={20} color={color} />
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{label}</span>
      </div>
      <p style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--text-primary)' }}>
        {value} <span style={{ fontSize: '0.875rem', fontWeight: '400' }}>{unit}</span>
      </p>
    </div>
  );
}

function FlightDetail() {
  const { id } = useParams();
  const [flight, setFlight] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFlightDetail();
  }, [id]);

  const fetchFlightDetail = async () => {
    try {
      setLoading(true);
      const data = await flightsAPI.getById(id);
      setFlight(data);
    } catch (error) {
      console.error('Error fetching flight detail:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading flight details...</div>;
  }

  if (!flight) {
    return <div className="error-message">Flight not found</div>;
  }

  const telemetry = flight.telemetry;
  const isGroundOnly = flight.is_ground_only || 
    (telemetry && [1, 2, 3, 4].every(m => telemetry[`motor${m}_max`] === null || telemetry[`motor${m}_max`] <= 1050));

  return (
    <div>
      <Link to="/flights" style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: '0.5rem',
        color: 'var(--primary-color)',
        textDecoration: 'none',
        marginBottom: '1rem',
        fontWeight: '500'
      }}>
        <ArrowLeft size={20} />
        Back to Flights
      </Link>

      {/* Header */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '1rem' }}>
          Flight #{flight.id}
        </h2>
        <div className="grid grid-4">
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Drone</p>
            <p style={{ fontWeight: '600' }}>{flight.drone_name}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Date</p>
            <p style={{ fontWeight: '600' }}>{formatDate(flight.flight_date)}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Duration</p>
            <p style={{ fontWeight: '600' }}>{formatDuration(flight.duration_seconds)}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Messages</p>
            <p style={{ fontWeight: '600' }}>{flight.total_messages.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Ground-Only / Disarmed Warning Banner */}
      {isGroundOnly && (
        <div className="card" style={{ 
          marginTop: '1.25rem',
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderLeft: '4px solid #f59e0b',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '1rem',
          padding: '1.25rem'
        }}>
          <AlertTriangle size={24} color="#f59e0b" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: '600', color: '#f59e0b' }}>
              Ground / Disarmed Session Detected
            </h4>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              No armed motor throttle (&gt;1050 µs) was recorded in this telemetry log. All motors remained at or below the idle disarmed threshold (1000 µs) throughout the recording. This file represents a bench test, pre-arm configuration, or disarmed replay rather than an airborne flight.
            </p>
          </div>
        </div>
      )}

      {telemetry && (
        <>
          {/* Motor Outputs */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '2rem 0 1rem' }}>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0 }}>
              Motor Outputs (PWM)
            </h3>
            {isGroundOnly && (
              <span style={{ 
                fontSize: '0.75rem', 
                backgroundColor: 'rgba(245, 158, 11, 0.15)', 
                color: '#f59e0b', 
                padding: '0.25rem 0.6rem', 
                borderRadius: '4px',
                fontWeight: '600'
              }}>
                DISARMED / IDLE (1000 µs)
              </span>
            )}
          </div>
          <div className="grid grid-4">
            {[1, 2, 3, 4].map(motorNum => {
              const avgVal = telemetry[`motor${motorNum}_avg`];
              const maxVal = telemetry[`motor${motorNum}_max`];
              return (
                <div key={motorNum} className="card">
                  <h4 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Gauge size={18} color="var(--primary-color)" />
                    Motor {motorNum}
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Average</p>
                      <p style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                        {avgVal != null ? `${formatNumber(avgVal, 0)} μs` : isGroundOnly ? '1000 μs (Idle)' : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Maximum</p>
                      <p style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                        {maxVal != null ? `${formatNumber(maxVal, 0)} μs` : isGroundOnly ? '1000 μs (Idle)' : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Battery Metrics */}
          <h3 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '2rem 0 1rem' }}>
            Battery Health
          </h3>
          {!(telemetry.battery_voltage_avg || telemetry.battery_current_avg || telemetry.battery_remaining_avg || telemetry.battery_internal_resistance_avg) ? (
            <p style={{ color: 'var(--text-secondary)', padding: '1rem 0' }}>
              ⚠️ No battery data found in this telemetry file. The file may not contain <code>BATTERY_STATUS</code> or <code>SYS_STATUS</code> messages with valid voltage readings.
            </p>
          ) : (
            <div className="grid grid-3">
              {telemetry.battery_voltage_avg != null && (
                <MetricCard
                  icon={Battery}
                  label="Average Voltage"
                  value={formatNumber(telemetry.battery_voltage_avg)}
                  unit="V"
                  color="var(--success-color)"
                />
              )}
              {telemetry.battery_voltage_min != null && (
                <MetricCard
                  icon={Battery}
                  label="Minimum Voltage"
                  value={formatNumber(telemetry.battery_voltage_min)}
                  unit="V"
                  color="var(--warning-color)"
                />
              )}
              {telemetry.battery_current_avg != null && (
                <MetricCard
                  icon={Activity}
                  label="Average Current"
                  value={formatNumber(telemetry.battery_current_avg)}
                  unit="A"
                  color="var(--info-color)"
                />
              )}
              {telemetry.battery_current_max != null && (
                <MetricCard
                  icon={Activity}
                  label="Peak Current"
                  value={formatNumber(telemetry.battery_current_max)}
                  unit="A"
                  color="var(--danger-color)"
                />
              )}
              {telemetry.battery_remaining_avg != null && (
                <MetricCard
                  icon={Battery}
                  label="Avg Battery Remaining"
                  value={formatNumber(telemetry.battery_remaining_avg, 0)}
                  unit="%"
                  color="var(--secondary-color)"
                />
              )}
              <MetricCard
                icon={Zap}
                label="Internal Resistance (Avg)"
                value={telemetry.battery_internal_resistance_avg != null 
                  ? formatNumber(telemetry.battery_internal_resistance_avg, 2) 
                  : 'N/A'}
                unit={telemetry.battery_internal_resistance_avg != null ? "mΩ" : ""}
                color="#f59e0b"
              />
              <MetricCard
                icon={Zap}
                label="Internal Resistance (Peak)"
                value={telemetry.battery_internal_resistance_max != null 
                  ? formatNumber(telemetry.battery_internal_resistance_max, 2) 
                  : 'N/A'}
                unit={telemetry.battery_internal_resistance_max != null ? "mΩ" : ""}
                color="#ef4444"
              />
            </div>
          )}

          {/* Vibration Metrics */}
          <h3 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '2rem 0 1rem' }}>
            Vibration Analysis
          </h3>
          <div className="grid grid-4">
            <MetricCard
              icon={Activity}
              label="Magnitude (Avg)"
              value={formatNumber(telemetry.vibration_magnitude_avg)}
              unit=""
              color="var(--secondary-color)"
            />
            <MetricCard
              icon={Activity}
              label="X-Axis (Avg)"
              value={formatNumber(telemetry.vibration_x_avg)}
              unit=""
              color="#ef4444"
            />
            <MetricCard
              icon={Activity}
              label="Y-Axis (Avg)"
              value={formatNumber(telemetry.vibration_y_avg)}
              unit=""
              color="#f59e0b"
            />
            <MetricCard
              icon={Activity}
              label="Z-Axis (Avg)"
              value={formatNumber(telemetry.vibration_z_avg)}
              unit=""
              color="#10b981"
            />
          </div>

          {/* GPS & Satellite Telemetry */}
          <h3 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '2rem 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Navigation size={22} color="var(--primary-color)" />
            GPS & Satellite Navigation
          </h3>

          {/* GPS Status Banner */}
          {telemetry.gps_status && (
            <div 
              className="card" 
              style={{ 
                marginBottom: '1.25rem',
                borderLeft: `5px solid ${
                  telemetry.gps_status === 'ok' 
                    ? 'var(--success-color)' 
                    : telemetry.gps_status === 'degraded' 
                    ? 'var(--warning-color)' 
                    : telemetry.gps_status === 'no_fix' 
                    ? 'var(--danger-color)' 
                    : 'var(--text-secondary)'
                }`,
                background: telemetry.gps_status === 'ok' 
                  ? 'rgba(16, 185, 129, 0.08)' 
                  : telemetry.gps_status === 'degraded' 
                  ? 'rgba(245, 158, 11, 0.08)' 
                  : telemetry.gps_status === 'no_fix' 
                  ? 'rgba(239, 68, 68, 0.08)' 
                  : 'var(--background)',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '1.1rem 1.25rem'
              }}
            >
              <div>
                {telemetry.gps_status === 'ok' && <CheckCircle size={30} color="var(--success-color)" />}
                {telemetry.gps_status === 'degraded' && <AlertCircle size={30} color="var(--warning-color)" />}
                {telemetry.gps_status === 'no_fix' && <XCircle size={30} color="var(--danger-color)" />}
                {telemetry.gps_status === 'no_data' && <Radio size={30} color="var(--text-secondary)" />}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
                  <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>
                    {telemetry.gps_status === 'ok' && 'GPS is working correctly & fine'}
                    {telemetry.gps_status === 'degraded' && 'Warning: GPS packets are not being received correctly'}
                    {telemetry.gps_status === 'no_fix' && 'GPS Error: No 3D Fix Acquired (Signal Lost)'}
                    {telemetry.gps_status === 'no_data' && 'No GPS Telemetry Available'}
                  </h4>
                  <span 
                    className={`badge ${
                      telemetry.gps_status === 'ok' 
                        ? 'badge-good' 
                        : telemetry.gps_status === 'degraded' 
                        ? 'badge-warning' 
                        : 'badge-danger'
                    }`}
                    style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}
                  >
                    {telemetry.gps_status_label || telemetry.gps_status?.toUpperCase()}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.925rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {telemetry.gps_status_message || (
                    telemetry.gps_status === 'ok'
                      ? 'GPS lock is solid. All position packets are being received with accurate 3D coordinates.'
                      : 'Packets are dropping or failing fix lock. Check GPS module antenna and cable connections.'
                  )}
                </p>
              </div>
            </div>
          )}

          {/* GPS Metrics Grid */}
          <div className="grid grid-4" style={{ marginBottom: '1.5rem' }}>
            <MetricCard
              icon={Radio}
              label="GPS Signal Status"
              value={
                telemetry.gps_status === 'ok' 
                  ? 'Healthy (3D)' 
                  : telemetry.gps_status === 'degraded' 
                  ? 'Degraded' 
                  : telemetry.gps_status === 'no_fix' 
                  ? 'No Fix' 
                  : 'N/A'
              }
              unit=""
              color={
                telemetry.gps_status === 'ok' 
                  ? 'var(--success-color)' 
                  : telemetry.gps_status === 'degraded' 
                  ? 'var(--warning-color)' 
                  : 'var(--danger-color)'
              }
            />
            <MetricCard
              icon={Radio}
              label="Packets Received"
              value={
                telemetry.gps_fix_count != null && telemetry.total_gps_messages != null
                  ? `${formatNumber(telemetry.gps_fix_count, 0)} / ${formatNumber(telemetry.total_gps_messages, 0)}`
                  : 'N/A'
              }
              unit="packets"
              color={telemetry.gps_status === 'ok' ? 'var(--success-color)' : 'var(--warning-color)'}
            />
            <MetricCard
              icon={Gauge}
              label="Fix Reception Rate"
              value={telemetry.gps_fix_ratio != null ? formatNumber(telemetry.gps_fix_ratio * 100, 1) : 'N/A'}
              unit="%"
              color={
                telemetry.gps_fix_ratio >= 0.90 
                  ? 'var(--success-color)' 
                  : telemetry.gps_fix_ratio >= 0.70 
                  ? 'var(--warning-color)' 
                  : 'var(--danger-color)'
              }
            />
            <MetricCard
              icon={Activity}
              label="Max Altitude"
              value={telemetry.altitude_max != null ? formatNumber(telemetry.altitude_max, 1) : 'N/A'}
              unit="m"
              color="var(--primary-color)"
            />
          </div>

          {/* Flight Speed & Temperature */}
          {(telemetry.speed_max || telemetry.temperature_avg) && (
            <>
              <h3 style={{ fontSize: '1.35rem', fontWeight: '600', margin: '1.5rem 0 1rem' }}>
                Speed & Thermal Performance
              </h3>
              <div className="grid grid-3">
                {telemetry.speed_max != null && (
                  <MetricCard
                    icon={Activity}
                    label="Max Flight Speed"
                    value={formatNumber(telemetry.speed_max, 1)}
                    unit="m/s"
                    color="var(--info-color)"
                  />
                )}
                {telemetry.speed_avg != null && (
                  <MetricCard
                    icon={Activity}
                    label="Avg Flight Speed"
                    value={formatNumber(telemetry.speed_avg, 1)}
                    unit="m/s"
                    color="var(--primary-color)"
                  />
                )}
                {telemetry.temperature_avg != null && (
                  <MetricCard
                    icon={Thermometer}
                    label="Avg Temperature"
                    value={formatNumber(telemetry.temperature_avg, 1)}
                    unit="°C"
                    color="var(--warning-color)"
                  />
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default FlightDetail;
