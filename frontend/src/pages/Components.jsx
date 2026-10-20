import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { componentsAPI, dronesAPI } from '../services/api';
import { ArrowLeft, Battery, Zap, Fan, Cpu, Plus, RefreshCw, AlertCircle } from 'lucide-react';
import { formatDate, formatNumber } from '../utils/helpers';

const COMPONENT_ICONS = {
  battery: Battery,
  motor: Zap,
  propeller: Fan,
  esc: Cpu
};

const STATUS_COLORS = {
  good: 'var(--success-color)',
  attention: 'var(--info-color)',
  replace_soon: 'var(--warning-color)',
  overdue: 'var(--danger-color)',
  replaced: 'var(--text-secondary)'
};

function Components() {
  const { droneId } = useParams();
  const [drone, setDrone] = useState(null);
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [replacing, setReplacing] = useState(null);

  useEffect(() => {
    if (droneId) {
      fetchData();
    }
  }, [droneId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [droneData, componentsData] = await Promise.all([
        dronesAPI.getById(droneId),
        componentsAPI.getByDrone(droneId, true)
      ]);
      setDrone(droneData);
      setComponents(componentsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReplace = async (componentId) => {
    const notes = prompt('Replacement notes (optional):');
    if (notes === null) return; // Cancelled

    try {
      setReplacing(componentId);
      await componentsAPI.replace(componentId, { notes });
      await fetchData();
      alert('Component replaced successfully!');
    } catch (error) {
      console.error('Error replacing component:', error);
      alert('Failed to replace component');
    } finally {
      setReplacing(null);
    }
  };

  if (loading) {
    return <div className="loading">Loading components...</div>;
  }

  if (!drone) {
    return <div className="error-message">Drone not found</div>;
  }

  return (
    <div>
      <Link
        to={`/drones/${droneId}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--primary-color)',
          textDecoration: 'none',
          marginBottom: '1rem',
          fontWeight: '500'
        }}
      >
        <ArrowLeft size={20} />
        Back to Drone Detail
      </Link>

      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
            Component Tracking
          </h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            {drone.name || drone.drone_id} - Battery cycles, motor hours, and component lifecycle
          </p>
        </div>
        <button
          onClick={() => setShowRegisterForm(true)}
          className="btn btn-primary"
        >
          <Plus size={18} />
          Register Component
        </button>
      </div>

      {components.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <AlertCircle size={48} color="var(--text-secondary)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Components Registered</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Start tracking batteries, motors, propellers, and ESCs for lifecycle management
          </p>
          <button onClick={() => setShowRegisterForm(true)} className="btn btn-primary">
            <Plus size={18} />
            Register First Component
          </button>
        </div>
      ) : (
        <div className="grid grid-2">
          {components.map(component => {
            const Icon = COMPONENT_ICONS[component.component_type] || Cpu;
            const statusColor = STATUS_COLORS[component.status] || 'var(--text-secondary)';
            const healthPercent = component.health_percentage || 0;

            return (
              <div key={component.id} className="card" style={{ borderLeft: `4px solid ${statusColor}` }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Icon size={32} color={statusColor} />
                    <div>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                        {component.component_name}
                      </h3>
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {component.component_type} {component.position && `• ${component.position}`}
                      </p>
                    </div>
                  </div>
                  <span className={`badge badge-${component.status === 'good' ? 'healthy' : component.status === 'overdue' ? 'critical' : 'warning'}`}>
                    {component.status}
                  </span>
                </div>

                {/* Health Bar */}
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>Health</span>
                    <span style={{ fontSize: '0.875rem', fontWeight: '600', color: statusColor }}>
                      {formatNumber(healthPercent, 0)}%
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: 'var(--background)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${healthPercent}%`,
                      height: '100%',
                      backgroundColor: statusColor,
                      transition: 'width 0.3s'
                    }} />
                  </div>
                </div>

                {/* Usage Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                      Flight Hours
                    </p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '700' }}>
                      {formatNumber(component.total_flight_hours, 1)}h
                      {component.max_flight_hours && (
                        <span style={{ fontSize: '0.75rem', fontWeight: '400', color: 'var(--text-secondary)' }}>
                          {' '}/ {component.max_flight_hours}h
                        </span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                      Flights
                    </p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '700' }}>
                      {component.total_flight_count}
                      {component.max_flight_count && (
                        <span style={{ fontSize: '0.75rem', fontWeight: '400', color: 'var(--text-secondary)' }}>
                          {' '}/ {component.max_flight_count}
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Battery Cycles (only for batteries) */}
                {component.component_type === 'battery' && (
                  <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'var(--background)', borderRadius: '0.375rem' }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                      Charge Cycles
                    </p>
                    <p style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                      {component.total_cycles}
                      {component.max_cycles && (
                        <span style={{ fontSize: '0.875rem', fontWeight: '400', color: 'var(--text-secondary)' }}>
                          {' '}/ {component.max_cycles} cycles
                        </span>
                      )}
                    </p>
                  </div>
                )}

                {/* Metadata */}
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                  {component.serial_number && (
                    <p>Serial: {component.serial_number}</p>
                  )}
                  <p>Installed: {formatDate(component.installed_date)}</p>
                </div>

                {/* Actions */}
                <button
                  onClick={() => handleReplace(component.id)}
                  className="btn btn-secondary"
                  style={{ width: '100%', justifyContent: 'center' }}
                  disabled={replacing === component.id}
                >
                  <RefreshCw size={16} />
                  {replacing === component.id ? 'Replacing...' : 'Mark as Replaced'}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Register Component Modal */}
      {showRegisterForm && (
        <RegisterComponentModal
          droneId={droneId}
          onClose={() => setShowRegisterForm(false)}
          onSuccess={() => {
            setShowRegisterForm(false);
            fetchData();
          }}
        />
      )}
    </div>
  );
}

function RegisterComponentModal({ droneId, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    component_type: 'battery',
    component_name: '',
    serial_number: '',
    position: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      await componentsAPI.register(droneId, formData);
      onSuccess();
    } catch (error) {
      console.error('Error registering component:', error);
      alert('Failed to register component');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="card" style={{ maxWidth: '500px', width: '90%', padding: '2rem', margin: 0 }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '1.5rem' }}>
          Register Component
        </h3>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
              Component Type *
            </label>
            <select
              value={formData.component_type}
              onChange={(e) => setFormData({ ...formData, component_type: e.target.value })}
              required
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
            >
              <option value="battery">Battery</option>
              <option value="motor">Motor</option>
              <option value="propeller">Propeller</option>
              <option value="esc">ESC</option>
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
              Component Name *
            </label>
            <input
              type="text"
              value={formData.component_name}
              onChange={(e) => setFormData({ ...formData, component_name: e.target.value })}
              placeholder="e.g., Battery-001, Motor Front Left"
              required
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
              Serial Number
            </label>
            <input
              type="text"
              value={formData.serial_number}
              onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
              placeholder="Optional"
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
              Position
            </label>
            <input
              type="text"
              value={formData.position}
              onChange={(e) => setFormData({ ...formData, position: e.target.value })}
              placeholder="e.g., front_left, rear_right"
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              style={{ flex: 1 }}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={submitting}
            >
              {submitting ? 'Registering...' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Components;
