# API Documentation

Complete API reference for the Drone Telemetry Parser backend.

Base URL: `http://localhost:8000/api`

## Authentication

Currently, the API does not require authentication. For production deployments, implement JWT or OAuth authentication.

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Telemetry Endpoints

### Upload Telemetry File

Upload and process a drone telemetry file.

**Endpoint:** `POST /api/telemetry/upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | File | Yes | .bin or .tlog telemetry file |
| drone_id | String | Yes | Unique identifier for the drone |
| drone_name | String | No | Human-readable name |
| run_analytics | Boolean | No | Run predictive analytics (default: true) |

**Example Request (curl):**
```bash
curl -X POST "http://localhost:8000/api/telemetry/upload" \
  -F "file=@flight.bin" \
  -F "drone_id=DRONE-001" \
  -F "drone_name=Phoenix Quadcopter" \
  -F "run_analytics=true"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Telemetry file processed successfully",
  "flight_id": 1,
  "drone_id": 1,
  "messages_processed": 15420,
  "duration_seconds": 320.5,
  "alerts_generated": 2,
  "alerts": [
    {
      "id": 1,
      "type": "motor",
      "component": "motor_1",
      "severity": "warning",
      "message": "Motor 1 average PWM output has increased 16.5% from baseline",
      "recommendation": "Motor 1 is working harder than normal. Check for propeller damage..."
    }
  ]
}
```

### Validate File

Check if a filename is valid for upload.

**Endpoint:** `GET /api/telemetry/validate-file/{filename}`

**Response (200 OK):**
```json
{
  "valid": true,
  "file_type": "bin"
}
```

## Drone Endpoints

### List All Drones

Get a list of all registered drones.

**Endpoint:** `GET /api/drones/`

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| skip | Integer | 0 | Number of records to skip |
| limit | Integer | 100 | Maximum records to return |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "drone_id": "DRONE-001",
    "name": "Phoenix Quadcopter",
    "model": "DJI Phantom 4",
    "serial_number": "SN123456",
    "total_flights": 45,
    "last_flight_date": "2026-09-25T10:30:00"
  }
]
```

### Get Drone Details

Get detailed information about a specific drone.

**Endpoint:** `GET /api/drones/{drone_id}`

**Response (200 OK):**
```json
{
  "id": 1,
  "drone_id": "DRONE-001",
  "name": "Phoenix Quadcopter",
  "model": "DJI Phantom 4",
  "serial_number": "SN123456",
  "total_flights": 45,
  "last_flight_date": "2026-09-25T10:30:00",
  "health_status": "warning",
  "alert_counts": {
    "critical": 0,
    "warning": 2,
    "info": 1
  },
  "total_unresolved_alerts": 3
}
```

### Get Drone Health Summary

Get health status and recent alerts for a drone.

**Endpoint:** `GET /api/drones/{drone_id}/health`

**Response (200 OK):**
```json
{
  "drone_id": 1,
  "health_status": "warning",
  "alert_counts": {
    "critical": 0,
    "warning": 2,
    "info": 1
  },
  "total_unresolved_alerts": 3,
  "recent_alerts": [
    {
      "id": 1,
      "type": "motor",
      "component": "motor_1",
      "severity": "warning",
      "message": "Motor 1 average PWM output has increased 16.5% from baseline",
      "created_at": "2026-09-25T10:35:00"
    }
  ]
}
```

### Update Drone

Update drone information.

**Endpoint:** `PUT /api/drones/{drone_id}`

**Request Body:**
```json
{
  "name": "Phoenix Quadcopter Updated",
  "model": "DJI Phantom 4 Pro",
  "serial_number": "SN123456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Drone updated successfully",
  "drone": { ... }
}
```

### Delete Drone

Delete a drone and all associated data.

**Endpoint:** `DELETE /api/drones/{drone_id}`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Drone DRONE-001 deleted successfully"
}
```

## Flight Endpoints

### List Flights

Get a list of flights, optionally filtered by drone.

**Endpoint:** `GET /api/flights/`

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| drone_id | Integer | Filter by drone ID |
| skip | Integer | Records to skip (default: 0) |
| limit | Integer | Max records (default: 50, max: 200) |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "drone_id": 1,
    "drone_name": "Phoenix Quadcopter",
    "flight_date": "2026-09-25T10:30:00",
    "duration_seconds": 320.5,
    "filename": "flight_001.bin",
    "file_type": "bin",
    "total_messages": 15420
  }
]
```

### Get Flight Details

Get detailed information and telemetry for a flight.

**Endpoint:** `GET /api/flights/{flight_id}`

**Response (200 OK):**
```json
{
  "id": 1,
  "drone_id": 1,
  "drone_name": "Phoenix Quadcopter",
  "flight_date": "2026-09-25T10:30:00",
  "duration_seconds": 320.5,
  "filename": "flight_001.bin",
  "file_type": "bin",
  "total_messages": 15420,
  "telemetry": {
    "motor1_avg": 1520.5,
    "motor1_max": 1850.0,
    "battery_voltage_avg": 14.8,
    "battery_voltage_min": 13.2,
    "battery_current_avg": 18.5,
    "battery_remaining_avg": 85.0,
    "battery_internal_resistance_avg": 12.4,
    "battery_internal_resistance_min": 8.1,
    "battery_internal_resistance_max": 15.6,
    "vibration_magnitude_avg": 12.5,
    ...
  }
}
```

### Get Flight Telemetry

Get only telemetry data for a flight.

**Endpoint:** `GET /api/flights/{flight_id}/telemetry`

### Delete Flight

Delete a flight and its telemetry data.

**Endpoint:** `DELETE /api/flights/{flight_id}`

## Analytics Endpoints

### Analyze Flight

Run predictive analytics on a specific flight.

**Endpoint:** `POST /api/analytics/analyze/{flight_id}`

**Response (200 OK):**
```json
{
  "success": true,
  "flight_id": 1,
  "alerts_generated": 2,
  "alerts": [ ... ]
}
```

### Get Motor Trends

Get motor output trends over time for a drone.

**Endpoint:** `GET /api/analytics/trends/motors/{drone_id}`

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| motor_number | Integer | Specific motor (1-4) or null for all |
| limit | Integer | Number of flights (default: 20) |

**Response (200 OK):**
```json
{
  "drone_id": 1,
  "drone_name": "Phoenix Quadcopter",
  "motor_number": null,
  "trends": [
    {
      "flight_id": 1,
      "flight_date": "2026-09-25T10:30:00",
      "motors": {
        "motor_1": { "avg": 1520.5, "max": 1850.0 },
        "motor_2": { "avg": 1518.2, "max": 1845.0 },
        "motor_3": { "avg": 1522.8, "max": 1855.0 },
        "motor_4": { "avg": 1519.1, "max": 1848.0 }
      }
    }
  ]
}
```

### Get Battery Trends

Get battery health trends for a drone.

**Endpoint:** `GET /api/analytics/trends/battery/{drone_id}`

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | Integer | Number of flights (default: 20) |

### Get Vibration Trends

Get vibration trends for a drone.

**Endpoint:** `GET /api/analytics/trends/vibration/{drone_id}`

### Compare Flights

Compare telemetry data between two flights.

**Endpoint:** `GET /api/analytics/compare/{drone_id}`

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| flight_id1 | Integer | Yes | First flight ID |
| flight_id2 | Integer | Yes | Second flight ID |

### Get Drone Statistics

Get overall statistics for a drone.

**Endpoint:** `GET /api/analytics/statistics/{drone_id}`

**Response (200 OK):**
```json
{
  "drone_id": 1,
  "drone_name": "Phoenix Quadcopter",
  "total_flights": 45,
  "total_flight_time_seconds": 14420,
  "total_flight_time_hours": 4.0,
  "averages": {
    "avg_motor_outputs": {
      "motor_1": 1520.5,
      "motor_2": 1518.2,
      "motor_3": 1522.8,
      "motor_4": 1519.1
    },
    "avg_battery_voltage": 14.6,
    "avg_vibration_magnitude": 11.8
  }
}
```

## Maintenance Endpoints

### List Alerts

Get maintenance alerts with optional filtering.

**Endpoint:** `GET /api/maintenance/`

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| drone_id | Integer | Filter by drone |
| severity | String | Filter by severity (info/warning/critical) |
| alert_type | String | Filter by type (motor/battery/vibration) |
| resolved | Boolean | Filter by resolution status |
| skip | Integer | Records to skip |
| limit | Integer | Max records (default: 50, max: 200) |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "drone_id": 1,
    "drone_name": "Phoenix Quadcopter",
    "flight_id": 1,
    "alert_type": "motor",
    "component": "motor_1",
    "severity": "warning",
    "metric_name": "motor1_avg_pwm",
    "current_value": 1620.5,
    "baseline_value": 1390.2,
    "deviation_percent": 16.5,
    "threshold_percent": 15.0,
    "message": "Motor 1 average PWM output has increased 16.5% from baseline",
    "recommendation": "Motor 1 is working harder than normal. Check for propeller damage...",
    "acknowledged": false,
    "resolved": false,
    "created_at": "2026-09-25T10:35:00"
  }
]
```

### Get Alert Details

Get detailed information about a specific alert.

**Endpoint:** `GET /api/maintenance/{alert_id}`

### Acknowledge Alert

Mark an alert as acknowledged.

**Endpoint:** `PATCH /api/maintenance/{alert_id}/acknowledge`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Alert acknowledged",
  "alert_id": 1
}
```

### Resolve Alert

Mark an alert as resolved.

**Endpoint:** `PATCH /api/maintenance/{alert_id}/resolve`

### Delete Alert

Delete an alert.

**Endpoint:** `DELETE /api/maintenance/{alert_id}`

### Get Alerts by Type

Get summary of unresolved alerts grouped by type.

**Endpoint:** `GET /api/maintenance/summary/by-type`

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| drone_id | Integer | Filter by drone (optional) |

**Response (200 OK):**
```json
{
  "drone_id": 1,
  "unresolved_alerts": 5,
  "by_type": {
    "motor": { "total": 2, "critical": 0, "warning": 2, "info": 0 },
    "battery": { "total": 2, "critical": 1, "warning": 1, "info": 0 },
    "vibration": { "total": 1, "critical": 0, "warning": 0, "info": 1 }
  }
}
```

### Get Alerts by Severity

Get alerts grouped by severity level.

**Endpoint:** `GET /api/maintenance/summary/by-severity`

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

## Rate Limiting

Currently no rate limiting is implemented. For production, implement rate limiting per IP or API key.

## Pagination

List endpoints support pagination via `skip` and `limit` parameters:
- Default limit: varies by endpoint (typically 50)
- Maximum limit: 200
- Use skip to paginate: `skip=0` (first page), `skip=50` (second page), etc.

---

For interactive API documentation, visit: http://localhost:8000/docs
