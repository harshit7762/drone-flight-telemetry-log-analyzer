import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { flightsAPI } from '../services/api';
import { Activity, Eye, Trash2 } from 'lucide-react';
import { formatDate, formatDuration } from '../utils/helpers';

function Flights() {
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchFlights();
  }, []);

  const fetchFlights = async () => {
    try {
      setLoading(true);
      const data = await flightsAPI.list(null, 0, 100);
      setFlights(data);
    } catch (error) {
      console.error('Error fetching flights:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (flight) => {
    setDeleteConfirm(flight);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;

    try {
      setDeleting(true);
      await flightsAPI.delete(deleteConfirm.id);
      
      // Remove from local state
      setFlights(flights.filter(f => f.id !== deleteConfirm.id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting flight:', error);
      alert('Failed to delete flight. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirm(null);
  };

  if (loading) {
    return <div className="loading">Loading flights...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          Flight History
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          View and analyze telemetry data from all flights
        </p>
      </div>

      {flights.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <Activity size={48} color="var(--text-secondary)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Flights Recorded</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Upload telemetry files to see flight history
          </p>
        </div>
      ) : (
        <div className="card">
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Flight ID</th>
                  <th>Drone</th>
                  <th>Date</th>
                  <th>Duration</th>
                  <th>File</th>
                  <th>Messages</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {flights.map(flight => (
                  <tr key={flight.id}>
                    <td style={{ fontWeight: '600' }}>#{flight.id}</td>
                    <td>
                      <Link to={`/drones/${flight.drone_id}`} style={{ color: 'var(--primary-color)', textDecoration: 'none' }}>
                        {flight.drone_name}
                      </Link>
                    </td>
                    <td>{formatDate(flight.flight_date)}</td>
                    <td>
                      <div>{formatDuration(flight.duration_seconds)}</div>
                      {flight.is_ground_only && (
                        <span style={{ 
                          fontSize: '0.6875rem', 
                          backgroundColor: 'rgba(245, 158, 11, 0.15)', 
                          color: '#f59e0b', 
                          padding: '0.1rem 0.4rem', 
                          borderRadius: '4px',
                          fontWeight: '600',
                          display: 'inline-block',
                          marginTop: '0.2rem'
                        }}>
                          Ground Log
                        </span>
                      )}
                      {flight.gps_status === 'ok' && (
                        <span style={{ 
                          fontSize: '0.6875rem', 
                          backgroundColor: 'rgba(16, 185, 129, 0.15)', 
                          color: '#10b981', 
                          padding: '0.1rem 0.4rem', 
                          borderRadius: '4px',
                          fontWeight: '600',
                          display: 'inline-block',
                          marginTop: '0.2rem',
                          marginLeft: flight.is_ground_only ? '0.3rem' : '0'
                        }}>
                          GPS: OK {flight.gps_fix_ratio != null ? `(${Math.round(flight.gps_fix_ratio * 100)}%)` : ''}
                        </span>
                      )}
                      {flight.gps_status === 'degraded' && (
                        <span style={{ 
                          fontSize: '0.6875rem', 
                          backgroundColor: 'rgba(245, 158, 11, 0.15)', 
                          color: '#f59e0b', 
                          padding: '0.1rem 0.4rem', 
                          borderRadius: '4px',
                          fontWeight: '600',
                          display: 'inline-block',
                          marginTop: '0.2rem',
                          marginLeft: flight.is_ground_only ? '0.3rem' : '0'
                        }}>
                          GPS: Degraded {flight.gps_fix_ratio != null ? `(${Math.round(flight.gps_fix_ratio * 100)}%)` : ''}
                        </span>
                      )}
                      {flight.gps_status === 'no_fix' && (
                        <span style={{ 
                          fontSize: '0.6875rem', 
                          backgroundColor: 'rgba(239, 68, 68, 0.15)', 
                          color: '#ef4444', 
                          padding: '0.1rem 0.4rem', 
                          borderRadius: '4px',
                          fontWeight: '600',
                          display: 'inline-block',
                          marginTop: '0.2rem',
                          marginLeft: flight.is_ground_only ? '0.3rem' : '0'
                        }}>
                          GPS: No Fix
                        </span>
                      )}
                    </td>
                    <td>
                      <span style={{ 
                        fontSize: '0.75rem', 
                        padding: '0.25rem 0.5rem',
                        backgroundColor: 'var(--background)',
                        borderRadius: '0.25rem'
                      }}>
                        {flight.filename}
                      </span>
                    </td>
                    <td>{flight.total_messages.toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Link to={`/flights/${flight.id}`} className="btn btn-primary" style={{ padding: '0.375rem 0.75rem' }}>
                          <Eye size={16} />
                          View
                        </Link>
                        <button
                          onClick={() => handleDeleteClick(flight)}
                          className="btn btn-danger"
                          style={{ padding: '0.375rem 0.75rem' }}
                          title="Delete flight log"
                        >
                          <Trash2 size={16} />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
              Delete Flight Log?
            </h3>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{ marginBottom: '0.75rem' }}>
                Are you sure you want to delete this flight?
              </p>
              
              <div style={{ 
                backgroundColor: 'var(--background)', 
                padding: '1rem', 
                borderRadius: '0.375rem',
                marginBottom: '1rem'
              }}>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <strong>Flight ID:</strong> #{deleteConfirm.id}
                </p>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <strong>Drone:</strong> {deleteConfirm.drone_name}
                </p>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <strong>Date:</strong> {formatDate(deleteConfirm.flight_date)}
                </p>
                <p style={{ fontSize: '0.875rem' }}>
                  <strong>File:</strong> {deleteConfirm.filename}
                </p>
              </div>

              <div className="alert alert-warning" style={{ marginBottom: '0' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                    ⚠️ This will delete:
                  </p>
                  <ul style={{ fontSize: '0.875rem', paddingLeft: '1.5rem', margin: 0 }}>
                    <li>Flight record from database</li>
                    <li>All telemetry data (motors, battery, vibrations)</li>
                    <li>Original uploaded file (.bin/.tlog)</li>
                  </ul>
                  <p style={{ fontSize: '0.875rem', marginTop: '0.75rem', fontStyle: 'italic' }}>
                    💡 Maintenance alerts will be kept for historical reference
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
                {deleting ? 'Deleting...' : 'Delete Flight'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Flights;
