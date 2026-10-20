import React, { useState, useEffect } from 'react';
import { maintenanceAPI } from '../services/api';
import { AlertTriangle, Check, X } from 'lucide-react';
import { formatDate, getSeverityColor, formatNumber } from '../utils/helpers';

function Maintenance() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ severity: 'all', resolved: false });

  useEffect(() => {
    fetchAlerts();
  }, [filter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filter.severity !== 'all') params.severity = filter.severity;
      if (filter.resolved !== 'all') params.resolved = filter.resolved;
      
      const data = await maintenanceAPI.list(params);
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await maintenanceAPI.acknowledge(alertId);
      fetchAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await maintenanceAPI.resolve(alertId);
      fetchAlerts();
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading maintenance alerts...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          Maintenance Alerts
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Predictive maintenance warnings and recommendations
        </p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: '0.875rem', fontWeight: '500', marginRight: '0.5rem' }}>
              Severity:
            </label>
            <select
              value={filter.severity}
              onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
              style={{
                padding: '0.5rem',
                borderRadius: '0.375rem',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)'
              }}
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          
          <div>
            <label style={{ fontSize: '0.875rem', fontWeight: '500', marginRight: '0.5rem' }}>
              Status:
            </label>
            <select
              value={filter.resolved}
              onChange={(e) => setFilter({ ...filter, resolved: e.target.value === 'true' ? true : e.target.value === 'false' ? false : 'all' })}
              style={{
                padding: '0.5rem',
                borderRadius: '0.375rem',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)'
              }}
            >
              <option value="false">Unresolved</option>
              <option value="true">Resolved</option>
              <option value="all">All</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <AlertTriangle size={48} color="var(--success-color)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Alerts Found</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            {filter.resolved === false 
              ? 'All systems are operating normally! ✓' 
              : 'No alerts match the selected filters'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {alerts.map(alert => (
            <div
              key={alert.id}
              className="card"
              style={{
                borderLeft: `4px solid ${getSeverityColor(alert.severity)}`,
                opacity: alert.resolved ? 0.6 : 1
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <span className={`badge badge-${alert.severity}`}>
                      {alert.severity}
                    </span>
                    <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {alert.drone_name} • {alert.component}
                    </span>
                    {alert.resolved && (
                      <span className="badge badge-healthy">
                        Resolved
                      </span>
                    )}
                  </div>
                  
                  <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                    {alert.message}
                  </h3>
                  
                  <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                    <span>
                      Current: <strong>{formatNumber(alert.current_value)}</strong>
                    </span>
                    <span>
                      Baseline: <strong>{formatNumber(alert.baseline_value)}</strong>
                    </span>
                    <span>
                      Deviation: <strong style={{ color: getSeverityColor(alert.severity) }}>
                        {alert.deviation_percent > 0 ? '+' : ''}{alert.deviation_percent.toFixed(1)}%
                      </strong>
                    </span>
                  </div>
                  
                  {alert.recommendation && (
                    <div style={{
                      backgroundColor: 'var(--background)',
                      padding: '0.75rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      marginTop: '0.75rem'
                    }}>
                      <strong>💡 Recommendation:</strong> {alert.recommendation}
                    </div>
                  )}
                  
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                    Created: {formatDate(alert.created_at)}
                  </p>
                </div>
                
                {!alert.resolved && (
                  <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="btn btn-secondary"
                        style={{ padding: '0.5rem 0.75rem' }}
                      >
                        <Check size={16} />
                        Acknowledge
                      </button>
                    )}
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="btn btn-success"
                      style={{ padding: '0.5rem 0.75rem' }}
                    >
                      <X size={16} />
                      Resolve
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Maintenance;
