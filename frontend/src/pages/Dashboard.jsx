import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dronesAPI, maintenanceAPI, flightsAPI } from '../services/api';
import { AlertTriangle, Activity, Plane, TrendingUp } from 'lucide-react';
import { formatRelativeTime, getSeverityColor, getHealthStatusColor } from '../utils/helpers';

function StatCard({ icon: Icon, label, value, color, link }) {
  const content = (
    <div className="card" style={{ 
      borderLeft: `4px solid ${color}`,
      cursor: link ? 'pointer' : 'default',
      transition: 'all 0.2s'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
            {label}
          </p>
          <p style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            {value}
          </p>
        </div>
        <Icon size={48} color={color} style={{ opacity: 0.2 }} />
      </div>
    </div>
  );

  return link ? <Link to={link} style={{ textDecoration: 'none' }}>{content}</Link> : content;
}

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDrones: 0,
    totalFlights: 0,
    criticalAlerts: 0,
    recentFlights: 0
  });
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [drones, setDrones] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch drones
      const dronesData = await dronesAPI.list(0, 100);
      setDrones(dronesData);
      
      // Fetch flights (up to 200 for accurate counts)
      const flightsData = await flightsAPI.list(null, 0, 200);
      
      // Fetch maintenance alerts (unresolved)
      const alertsData = await maintenanceAPI.list({ resolved: false, limit: 100 });
      setRecentAlerts(alertsData.slice(0, 5));
      
      // Calculate stats
      const criticalCount = alertsData.filter(a => a.severity === 'critical').length;
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const recentCount = flightsData.filter(f => new Date(f.flight_date) >= sevenDaysAgo).length;
      
      setStats({
        totalDrones: dronesData.length,
        totalFlights: flightsData.length,
        criticalAlerts: criticalCount,
        recentFlights: recentCount > 0 ? recentCount : Math.min(flightsData.length, 5)
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          Dashboard
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Overview of your drone fleet and maintenance status
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard
          icon={Plane}
          label="Total Drones"
          value={stats.totalDrones}
          color="var(--primary-color)"
          link="/drones"
        />
        <StatCard
          icon={Activity}
          label="Total Flights"
          value={stats.totalFlights}
          color="var(--secondary-color)"
          link="/flights"
        />
        <StatCard
          icon={AlertTriangle}
          label="Critical Alerts"
          value={stats.criticalAlerts}
          color="var(--danger-color)"
          link="/maintenance"
        />
        <StatCard
          icon={TrendingUp}
          label="Recent Flights"
          value={stats.recentFlights}
          color="var(--success-color)"
        />
      </div>

      <div className="grid grid-2">
        {/* Drones Health Status */}
        <div className="card">
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            Drone Fleet Status
          </h3>
          
          {drones.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
              No drones registered yet. <Link to="/upload">Upload telemetry</Link> to get started.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {drones.slice(0, 5).map(drone => (
                <Link
                  key={drone.id}
                  to={`/drones/${drone.id}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem',
                    backgroundColor: 'var(--background)',
                    borderRadius: '0.375rem',
                    textDecoration: 'none',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e2e8f0'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--background)'}
                >
                  <div>
                    <p style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                      {drone.name || drone.drone_id}
                    </p>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {drone.total_flights} flights • Last flight {formatRelativeTime(drone.last_flight_date)}
                    </p>
                  </div>
                  <Plane size={20} color="var(--primary-color)" />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            Recent Maintenance Alerts
          </h3>
          
          {recentAlerts.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
              No unresolved alerts. All systems operational! ✓
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recentAlerts.map(alert => (
                <div
                  key={alert.id}
                  style={{
                    padding: '0.75rem',
                    backgroundColor: 'var(--background)',
                    borderRadius: '0.375rem',
                    borderLeft: `4px solid ${getSeverityColor(alert.severity)}`
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span className={`badge badge-${alert.severity}`}>
                      {alert.severity}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {formatRelativeTime(alert.created_at)}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                    {alert.drone_name} - {alert.component}
                  </p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    {alert.message}
                  </p>
                </div>
              ))}
            </div>
          )}
          
          {recentAlerts.length > 0 && (
            <Link
              to="/maintenance"
              style={{
                display: 'block',
                textAlign: 'center',
                marginTop: '1rem',
                color: 'var(--primary-color)',
                fontWeight: '500',
                textDecoration: 'none'
              }}
            >
              View all alerts →
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
