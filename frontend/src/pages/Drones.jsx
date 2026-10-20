import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { dronesAPI } from '../services/api';
import { Plane, AlertCircle, Trash2 } from 'lucide-react';
import { formatRelativeTime, getHealthStatusColor } from '../utils/helpers';

function Drones() {
  const [drones, setDrones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDrones();
  }, []);

  const fetchDrones = async () => {
    try {
      setLoading(true);
      const data = await dronesAPI.list();
      setDrones(data);
    } catch (error) {
      console.error('Error fetching drones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (e, drone) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteConfirm(drone);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;

    try {
      setDeleting(true);
      await dronesAPI.delete(deleteConfirm.id);
      
      // Remove from local state
      setDrones(drones.filter(d => d.id !== deleteConfirm.id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting drone:', error);
      alert('Failed to delete drone. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirm(null);
  };

  if (loading) {
    return <div className="loading">Loading drones...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
            Drone Fleet
          </h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            Manage and monitor your drones
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <Plane size={18} />
          Upload Telemetry
        </Link>
      </div>

      {drones.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <AlertCircle size={48} color="var(--text-secondary)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Drones Yet</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Upload telemetry data to register your first drone
          </p>
          <Link to="/upload" className="btn btn-primary">
            <Plane size={18} />
            Upload Telemetry
          </Link>
        </div>
      ) : (
        <div className="grid grid-3">
          {drones.map(drone => (
            <div
              key={drone.id}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 0.2s, box-shadow 0.2s',
                border: '1px solid var(--border)'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <Link
                to={`/drones/${drone.id}`}
                style={{
                  textDecoration: 'none',
                  color: 'inherit',
                  display: 'block'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <Plane size={32} color="var(--primary-color)" />
                  <span className="badge badge-info">
                    {drone.total_flights} {drone.total_flights === 1 ? 'flight' : 'flights'}
                  </span>
                </div>
                
                <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                  {drone.name || drone.drone_id}
                </h3>
                
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  ID: {drone.drone_id}
                </p>
                
                {drone.last_flight_date && (
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    Last flight: {formatRelativeTime(drone.last_flight_date)}
                  </p>
                )}
              </Link>

              {/* Bottom Actions Bar */}
              <div style={{
                marginTop: '1.25rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <Link
                  to={`/drones/${drone.id}`}
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--primary-color)',
                    textDecoration: 'none',
                    fontWeight: '500'
                  }}
                >
                  View Details →
                </Link>

                <button
                  onClick={(e) => handleDeleteClick(e, drone)}
                  className="btn btn-danger"
                  style={{
                    padding: '0.375rem 0.75rem',
                    fontSize: '0.8125rem'
                  }}
                  title="Delete drone"
                >
                  <Trash2 size={14} />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
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
          <div className="card" style={{
            maxWidth: '500px',
            width: '90%',
            padding: '2rem',
            margin: 0
          }}>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '1rem', color: 'var(--danger-color)' }}>
              Delete Drone?
            </h3>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{ marginBottom: '0.75rem' }}>
                Are you sure you want to delete this drone and all its data?
              </p>
              
              <div style={{ 
                backgroundColor: 'var(--background)', 
                padding: '1rem', 
                borderRadius: '0.375rem',
                marginBottom: '1rem'
              }}>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <strong>Drone:</strong> {deleteConfirm.name || deleteConfirm.drone_id}
                </p>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <strong>Drone ID:</strong> {deleteConfirm.drone_id}
                </p>
                <p style={{ fontSize: '0.875rem' }}>
                  <strong>Total Flights:</strong> {deleteConfirm.total_flights}
                </p>
              </div>

              <div className="alert alert-critical" style={{ marginBottom: '0' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                    ⚠️ This will permanently delete:
                  </p>
                  <ul style={{ fontSize: '0.875rem', paddingLeft: '1.5rem', margin: 0 }}>
                    <li>Drone record from database</li>
                    <li><strong>All {deleteConfirm.total_flights} flight records</strong></li>
                    <li>All telemetry data (motors, battery, vibrations)</li>
                    <li>All uploaded files (.bin/.tlog)</li>
                    <li>All maintenance alerts (resolved and unresolved)</li>
                  </ul>
                  <p style={{ fontSize: '0.875rem', marginTop: '0.75rem', fontWeight: '600' }}>
                    🔴 This action cannot be undone!
                  </p>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={handleDeleteCancel}
                className="btn btn-secondary"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="btn btn-danger"
                disabled={deleting}
              >
                <Trash2 size={16} />
                {deleting ? 'Deleting...' : 'Delete Drone'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Drones;
