import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { dronesAPI, analyticsAPI, maintenanceAPI } from '../services/api';
import TrendChart from '../components/TrendChart';
import { ArrowLeft, AlertTriangle, Activity, Battery, Gauge, Zap } from 'lucide-react';
import { formatDate, formatNumber, getHealthStatusColor } from '../utils/helpers';

function DroneDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [drone, setDrone] = useState(null);
  const [motorTrends, setMotorTrends] = useState(null);
  const [batteryTrends, setBatteryTrends] = useState(null);
  const [vibrationTrends, setVibrationTrends] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    fetchDroneData();
  }, [id]);

  const fetchDroneData = async () => {
    try {
      setLoading(true);
      
      const [droneData, motorData, batteryData, vibrationData, alertsData, statsData] = await Promise.all([
        dronesAPI.getById(id),
        analyticsAPI.getMotorTrends(id, null, 15),
        analyticsAPI.getBatteryTrends(id, 15),
        analyticsAPI.getVibrationTrends(id, 15),
        maintenanceAPI.list({ drone_id: id, resolved: false, limit: 10 }),
        analyticsAPI.getStatistics(id)
      ]);
      
      setDrone(droneData);
      setMotorTrends(motorData);
      setBatteryTrends(batteryData);
      setVibrationTrends(vibrationData);
      setAlerts(alertsData);
      setStatistics(statsData);
      
    } catch (error) {
      console.error('Error fetching drone data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading drone details...</div>;
  }

  if (!drone) {
    return <div className="error-message">Drone not found</div>;
  }

  // Prepare motor trend data
  const motorChartData = motorTrends?.trends?.length > 0 ? {
    labels: motorTrends.trends.map(t => formatDate(t.flight_date).split(' ')[0]),
    datasets: [1, 2, 3, 4].map(motorNum => ({
      label: `Motor ${motorNum} Avg`,
      data: motorTrends.trends.map(t => t.motors[`motor_${motorNum}`]?.avg || null),
      borderColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6'][motorNum - 1],
      backgroundColor: ['#ef444420', '#f59e0b20', '#10b98120', '#3b82f620'][motorNum - 1],
    }))
  } : null;

  // Prepare battery trend data
  const batteryChartData = batteryTrends?.trends?.length > 0 ? {
    labels: batteryTrends.trends.map(t => formatDate(t.flight_date).split(' ')[0]),
    datasets: [
      {
        label: 'Avg Voltage (V)',
        data: batteryTrends.trends.map(t => t.voltage_avg),
        borderColor: '#10b981',
        backgroundColor: '#10b98120',
      },
      {
        label: 'Min Voltage (V)',
        data: batteryTrends.trends.map(t => t.voltage_min),
        borderColor: '#ef4444',
        backgroundColor: '#ef444420',
      }
    ]
  } : null;

  // Prepare battery internal resistance trend data
  const resistanceChartData = (batteryTrends?.trends?.some(t => t.internal_resistance_avg != null)) ? {
    labels: batteryTrends.trends.map(t => formatDate(t.flight_date).split(' ')[0]),
    datasets: [
      {
        label: 'Internal Resistance (mΩ)',
        data: batteryTrends.trends.map(t => t.internal_resistance_avg),
        borderColor: '#f59e0b',
        backgroundColor: '#f59e0b20',
      }
    ]
  } : null;

  // Prepare vibration trend data
  const vibrationChartData = vibrationTrends?.trends?.length > 0 ? {
    labels: vibrationTrends.trends.map(t => formatDate(t.flight_date).split(' ')[0]),
    datasets: [
      {
        label: 'Magnitude Avg',
        data: vibrationTrends.trends.map(t => t.magnitude_avg),
        borderColor: '#8b5cf6',
        backgroundColor: '#8b5cf620',
      }
    ]
  } : null;

  return (
    <div>
      <Link to="/drones" style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: '0.5rem',
        color: 'var(--primary-color)',
        textDecoration: 'none',
        marginBottom: '1rem',
        fontWeight: '500'
      }}>
        <ArrowLeft size={20} />
        Back to Drones
      </Link>

      {/* Header */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
              {drone.name || drone.drone_id}
            </h2>
            <p style={{ color: 'var(--text-secondary)' }}>
              Drone ID: {drone.drone_id}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <Link to={`/drones/${id}/components`} className="btn btn-secondary">
              <Battery size={18} />
              Components
            </Link>
            <span className={`badge badge-${drone.health_status}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
              {drone.health_status}
            </span>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-3" style={{ marginBottom: '1.5rem' }}>
          <div className="card">
            <Activity size={24} color="var(--primary-color)" style={{ marginBottom: '0.5rem' }} />
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Total Flights
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: '700' }}>
              {statistics.total_flights}
            </p>
          </div>
          <div className="card">
            <Battery size={24} color="var(--success-color)" style={{ marginBottom: '0.5rem' }} />
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Flight Time
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: '700' }}>
              {formatNumber(statistics.total_flight_time_hours, 1)} hrs
            </p>
          </div>
          <div className="card">
            <AlertTriangle size={24} color="var(--danger-color)" style={{ marginBottom: '0.5rem' }} />
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Unresolved Alerts
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: '700' }}>
              {drone.total_unresolved_alerts}
            </p>
          </div>
        </div>
      )}

      {/* Charts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {motorChartData && (
          <div className="card">
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Gauge size={20} color="var(--primary-color)" />
              Motor Output Trends (PWM)
            </h3>
            <TrendChart
              labels={motorChartData.labels}
              datasets={motorChartData.datasets}
              yAxisLabel="PWM (μs)"
            />
          </div>
        )}

        {batteryChartData && (
          <div className="card">
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Battery size={20} color="var(--success-color)" />
              Battery Health Trends
            </h3>
            <TrendChart
              labels={batteryChartData.labels}
              datasets={batteryChartData.datasets}
              yAxisLabel="Voltage (V)"
            />
          </div>
        )}

        {resistanceChartData && (
          <div className="card">
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Zap size={20} color="#f59e0b" />
              Battery Internal Resistance Trends
            </h3>
            <TrendChart
              labels={resistanceChartData.labels}
              datasets={resistanceChartData.datasets}
              yAxisLabel="Resistance (mΩ)"
            />
          </div>
        )}

        {vibrationChartData && (
          <div className="card">
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={20} color="var(--secondary-color)" />
              Vibration Trends
            </h3>
            <TrendChart
              labels={vibrationChartData.labels}
              datasets={vibrationChartData.datasets}
              yAxisLabel="Magnitude"
            />
          </div>
        )}
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            Active Maintenance Alerts
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {alerts.map(alert => (
              <div key={alert.id} className={`alert alert-${alert.severity}`}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                    {alert.component} - {alert.severity.toUpperCase()}
                  </p>
                  <p style={{ fontSize: '0.875rem' }}>{alert.message}</p>
                  {alert.recommendation && (
                    <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', fontStyle: 'italic' }}>
                      💡 {alert.recommendation}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DroneDetail;
