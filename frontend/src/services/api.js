import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Telemetry API
export const telemetryAPI = {
  uploadFile: async (file, droneId, droneName, runAnalytics = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('drone_id', droneId);
    if (droneName) formData.append('drone_name', droneName);
    formData.append('run_analytics', runAnalytics);

    const response = await api.post('/telemetry/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  validateFile: async (filename) => {
    const response = await api.get(`/telemetry/validate-file/${filename}`);
    return response.data;
  },
};

// Drones API
export const dronesAPI = {
  list: async (skip = 0, limit = 100) => {
    const response = await api.get('/drones/', { params: { skip, limit } });
    return response.data;
  },

  getById: async (droneId) => {
    const response = await api.get(`/drones/${droneId}`);
    return response.data;
  },

  getHealth: async (droneId) => {
    const response = await api.get(`/drones/${droneId}/health`);
    return response.data;
  },

  update: async (droneId, data) => {
    const response = await api.put(`/drones/${droneId}`, data);
    return response.data;
  },

  delete: async (droneId) => {
    const response = await api.delete(`/drones/${droneId}`);
    return response.data;
  },
};

// Flights API
export const flightsAPI = {
  list: async (droneId = null, skip = 0, limit = 50) => {
    const params = { skip, limit };
    if (droneId) params.drone_id = droneId;
    const response = await api.get('/flights/', { params });
    return response.data;
  },

  getById: async (flightId) => {
    const response = await api.get(`/flights/${flightId}`);
    return response.data;
  },

  getTelemetry: async (flightId) => {
    const response = await api.get(`/flights/${flightId}/telemetry`);
    return response.data;
  },

  delete: async (flightId) => {
    const response = await api.delete(`/flights/${flightId}`);
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  analyzeFlight: async (flightId) => {
    const response = await api.post(`/analytics/analyze/${flightId}`);
    return response.data;
  },

  getMotorTrends: async (droneId, motorNumber = null, limit = 20) => {
    const params = { limit };
    if (motorNumber) params.motor_number = motorNumber;
    const response = await api.get(`/analytics/trends/motors/${droneId}`, { params });
    return response.data;
  },

  getBatteryTrends: async (droneId, limit = 20) => {
    const response = await api.get(`/analytics/trends/battery/${droneId}`, { params: { limit } });
    return response.data;
  },

  getVibrationTrends: async (droneId, limit = 20) => {
    const response = await api.get(`/analytics/trends/vibration/${droneId}`, { params: { limit } });
    return response.data;
  },

  compareFlights: async (droneId, flightId1, flightId2) => {
    const response = await api.get(`/analytics/compare/${droneId}`, {
      params: { flight_id1: flightId1, flight_id2: flightId2 },
    });
    return response.data;
  },

  getStatistics: async (droneId) => {
    const response = await api.get(`/analytics/statistics/${droneId}`);
    return response.data;
  },
};

// Components API
export const componentsAPI = {
  register: async (droneId, componentData) => {
    const response = await api.post(`/components/register?drone_id=${droneId}`, componentData);
    return response.data;
  },

  getByDrone: async (droneId, activeOnly = true, componentType = null) => {
    const params = { active_only: activeOnly };
    if (componentType) params.component_type = componentType;
    const response = await api.get(`/components/drone/${droneId}`, { params });
    return response.data;
  },

  getById: async (componentId) => {
    const response = await api.get(`/components/${componentId}`);
    return response.data;
  },

  replace: async (componentId, data) => {
    const response = await api.post(`/components/${componentId}/replace`, data);
    return response.data;
  },

  update: async (componentId, data) => {
    const response = await api.put(`/components/${componentId}`, data);
    return response.data;
  },

  delete: async (componentId) => {
    const response = await api.delete(`/components/${componentId}`);
    return response.data;
  },

  getFleetSummary: async () => {
    const response = await api.get('/components/fleet/summary');
    return response.data;
  },
};

// Maintenance API
export const maintenanceAPI = {
  list: async (filters = {}) => {
    const response = await api.get('/maintenance/', { params: filters });
    return response.data;
  },

  getById: async (alertId) => {
    const response = await api.get(`/maintenance/${alertId}`);
    return response.data;
  },

  acknowledge: async (alertId) => {
    const response = await api.patch(`/maintenance/${alertId}/acknowledge`);
    return response.data;
  },

  resolve: async (alertId) => {
    const response = await api.patch(`/maintenance/${alertId}/resolve`);
    return response.data;
  },

  delete: async (alertId) => {
    const response = await api.delete(`/maintenance/${alertId}`);
    return response.data;
  },

  getByType: async (droneId = null) => {
    const params = droneId ? { drone_id: droneId } : {};
    const response = await api.get('/maintenance/summary/by-type', { params });
    return response.data;
  },

  getBySeverity: async (droneId = null) => {
    const params = droneId ? { drone_id: droneId } : {};
    const response = await api.get('/maintenance/summary/by-severity', { params });
    return response.data;
  },
};

export default api;
