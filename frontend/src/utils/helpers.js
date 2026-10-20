import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
};

export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'N/A';
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
};

export const formatDuration = (seconds) => {
  if (!seconds) return 'N/A';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

export const getSeverityColor = (severity) => {
  const colors = {
    critical: 'var(--danger-color)',
    warning: 'var(--warning-color)',
    info: 'var(--info-color)',
  };
  return colors[severity] || 'var(--text-secondary)';
};

export const getHealthStatusColor = (status) => {
  const colors = {
    healthy: 'var(--success-color)',
    attention: 'var(--info-color)',
    warning: 'var(--warning-color)',
    critical: 'var(--danger-color)',
  };
  return colors[status] || 'var(--text-secondary)';
};

export const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  const num = Number(value);
  if (isNaN(num)) return 'N/A';
  const abs = Math.abs(num);
  if (abs > 0 && abs < 0.01) {
    return num.toFixed(4);
  }
  return num.toFixed(decimals);
};

export const getAlertIcon = (severity) => {
  // Returns appropriate icon name based on severity
  return severity === 'critical' ? '🔴' : severity === 'warning' ? '⚠️' : 'ℹ️';
};

export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const downloadFile = (data, filename, mimeType = 'application/json') => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
