import React, { useState } from 'react';
import { telemetryAPI } from '../services/api';
import { Upload as UploadIcon, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [droneId, setDroneId] = useState('');
  const [droneName, setDroneName] = useState('');
  const [runAnalytics, setRunAnalytics] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop().toLowerCase();
      if (ext === 'bin' || ext === 'tlog') {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Invalid file type. Only .bin and .tlog files are supported.');
        setFile(null);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file || !droneId) {
      setError('Please select a file and enter a drone ID');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setResult(null);

      const response = await telemetryAPI.uploadFile(
        file,
        droneId,
        droneName || null,
        runAnalytics
      );

      setResult(response);
      
      // Reset form
      setFile(null);
      setDroneId('');
      setDroneName('');
      document.getElementById('file-input').value = '';
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          Upload Telemetry
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload drone flight logs (.bin or .tlog files) for analysis
        </p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
                Telemetry File *
              </label>
              <input
                id="file-input"
                type="file"
                accept=".bin,.tlog"
                onChange={handleFileChange}
              />
              <label htmlFor="file-input" className="file-upload-label">
                <UploadIcon size={18} />
                {file ? file.name : 'Choose File'}
              </label>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Supported formats: .bin, .tlog (max 100MB)
              </p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
                Drone ID *
              </label>
              <input
                type="text"
                value={droneId}
                onChange={(e) => setDroneId(e.target.value)}
                placeholder="e.g., DRONE-001"
                required
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.375rem',
                  fontSize: '1rem'
                }}
              />
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Unique identifier for this drone
              </p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem' }}>
                Drone Name (Optional)
              </label>
              <input
                type="text"
                value={droneName}
                onChange={(e) => setDroneName(e.target.value)}
                placeholder="e.g., Phoenix Quadcopter"
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.375rem',
                  fontSize: '1rem'
                }}
              />
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Human-readable name for easier identification
              </p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={runAnalytics}
                  onChange={(e) => setRunAnalytics(e.target.checked)}
                  style={{ width: '1.25rem', height: '1.25rem' }}
                />
                <span style={{ fontWeight: '600' }}>Run predictive analytics</span>
              </label>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginLeft: '1.75rem' }}>
                Automatically analyze flight data and generate maintenance alerts
              </p>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading || !file || !droneId}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {uploading ? (
                <>
                  <Loader size={18} style={{ animation: 'spin 1s linear infinite' }} />
                  Processing...
                </>
              ) : (
                <>
                  <UploadIcon size={18} />
                  Upload and Process
                </>
              )}
            </button>
          </form>
        </div>

        <div>
          {/* Success Message */}
          {result && (
            <div className="alert alert-success">
              <CheckCircle size={24} />
              <div style={{ flex: 1 }}>
                <h3 style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                  Upload Successful!
                </h3>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                  Processed {result.messages_processed?.toLocaleString()} messages 
                  {result.duration_seconds && ` (${Math.floor(result.duration_seconds)}s flight)`}
                </p>
                {result.alerts_generated > 0 && (
                  <p style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                    ⚠️ {result.alerts_generated} maintenance alert{result.alerts_generated > 1 ? 's' : ''} generated
                  </p>
                )}
                <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => navigate(`/flights/${result.flight_id}`)}
                    className="btn btn-primary"
                    style={{ fontSize: '0.875rem', padding: '0.5rem 0.75rem' }}
                  >
                    View Flight Details
                  </button>
                  <button
                    onClick={() => navigate(`/drones/${result.drone_id}`)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.875rem', padding: '0.5rem 0.75rem' }}
                  >
                    View Drone
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert alert-critical">
              <AlertCircle size={24} />
              <div>
                <h3 style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Upload Failed</h3>
                <p style={{ fontSize: '0.875rem' }}>{error}</p>
              </div>
            </div>
          )}

          {/* Information */}
          <div className="card">
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
              📋 How It Works
            </h3>
            <ol style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <li style={{ fontSize: '0.875rem' }}>
                <strong>Upload</strong> your drone's telemetry file (.bin or .tlog format)
              </li>
              <li style={{ fontSize: '0.875rem' }}>
                <strong>Parse</strong> - We extract motor outputs, battery metrics, IMU vibrations, and more
              </li>
              <li style={{ fontSize: '0.875rem' }}>
                <strong>Analyze</strong> - Rolling-average comparison detects anomalies
              </li>
              <li style={{ fontSize: '0.875rem' }}>
                <strong>Alert</strong> - Receive predictive maintenance warnings with recommendations
              </li>
            </ol>
          </div>

          <div className="card" style={{ marginTop: '1rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
              🔍 What We Analyze
            </h3>
            <ul style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <li style={{ fontSize: '0.875rem' }}>Motor PWM outputs (workload detection)</li>
              <li style={{ fontSize: '0.875rem' }}>Battery voltage and current (degradation)</li>
              <li style={{ fontSize: '0.875rem' }}>IMU vibrations (mechanical issues)</li>
              <li style={{ fontSize: '0.875rem' }}>Cell voltage balance</li>
              <li style={{ fontSize: '0.875rem' }}>GPS altitude and speed</li>
              <li style={{ fontSize: '0.875rem' }}>Temperature readings</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Upload;
