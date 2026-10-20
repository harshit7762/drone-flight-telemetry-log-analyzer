import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Drones from './pages/Drones';
import DroneDetail from './pages/DroneDetail';
import Flights from './pages/Flights';
import FlightDetail from './pages/FlightDetail';
import Maintenance from './pages/Maintenance';
import Upload from './pages/Upload';
import Components from './pages/Components';
import { Home, Plane, Upload as UploadIcon, AlertTriangle, Activity } from 'lucide-react';

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/drones', icon: Plane, label: 'Drones' },
    { path: '/flights', icon: Activity, label: 'Flights' },
    { path: '/maintenance', icon: AlertTriangle, label: 'Maintenance' },
    { path: '/upload', icon: UploadIcon, label: 'Upload' },
  ];

  return (
    <nav style={{
      backgroundColor: 'var(--surface)',
      borderBottom: '1px solid var(--border)',
      padding: '1rem 0',
      marginBottom: '2rem',
      boxShadow: '0 1px 3px var(--shadow)'
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plane size={32} color="var(--primary-color)" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary-color)' }}>
            Drone Telemetry
          </h1>
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {navItems.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive ? 'var(--primary-color)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? '#eff6ff' : 'transparent',
                  fontWeight: isActive ? '600' : '500',
                  transition: 'all 0.2s'
                }}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--background)' }}>
        <Navigation />
        
        <div className="container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/drones" element={<Drones />} />
            <Route path="/drones/:id" element={<DroneDetail />} />
            <Route path="/drones/:droneId/components" element={<Components />} />
            <Route path="/flights" element={<Flights />} />
            <Route path="/flights/:id" element={<FlightDetail />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/upload" element={<Upload />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
