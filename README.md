# Drone Telemetry Parser and Predictive Maintenance System

A full-stack web application for analyzing drone flight telemetry data and providing predictive maintenance alerts. The system parses binary telemetry files (.bin/.tlog), extracts high-frequency time-series data, performs statistical analysis, and generates actionable maintenance recommendations using rolling-average comparison algorithms.

![Architecture](https://img.shields.io/badge/Architecture-Full%20Stack-blue)
![Backend](https://img.shields.io/badge/Backend-Python%20FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-React%2018-blue)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-orange)

## 🌟 Features

### Telemetry Parsing
- **Binary File Support**: Parse .bin and .tlog MAVLink telemetry files
- **Comprehensive Data Extraction**:
  - Motor PWM outputs (SERVO_OUTPUT_RAW, RCOU messages)
  - Battery metrics (voltage, current, cell voltages)
  - IMU vibration data (3-axis accelerometer readings)
  - GPS altitude and speed
  - Temperature readings
- **Statistical Analysis**: Calculate averages, maximums, and other metrics for each flight

### Predictive Maintenance
- **Rolling-Average Comparison**: Compare current flight metrics against historical baselines
- **Threshold-Based Detection**: Configurable thresholds for anomaly detection
- **Component-Specific Alerts**:
  - Motor workload analysis (PWM drift detection)
  - Battery health degradation tracking
  - Vibration anomaly detection (mechanical issues)
- **Severity Levels**: Info, Warning, and Critical alerts with actionable recommendations

### Interactive Dashboard
- **Real-time Visualization**: Interactive charts using Chart.js
- **Trend Analysis**: Motor output, battery health, and vibration trends over time
- **Fleet Management**: Monitor multiple drones from a single dashboard
- **Alert Management**: Acknowledge and resolve maintenance alerts

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React         │ HTTP    │   FastAPI       │  SQL    │   PostgreSQL    │
│   Frontend      │◄───────►│   Backend       │◄───────►│   Database      │
│   (Port 3000)   │         │   (Port 8000)   │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                            │
        │                            │
        ▼                            ▼
  Chart.js                      pymavlink
  Visualizations                Telemetry Parser
```

### Tech Stack

**Backend:**
- FastAPI (REST API framework)
- SQLAlchemy (ORM)
- PostgreSQL / SQLite (Database)
- pymavlink (MAVLink telemetry parsing)
- NumPy & Pandas (Data analysis)
- Pydantic (Data validation)

**Frontend:**
- React 18
- React Router v6 (Routing)
- Axios (HTTP client)
- Chart.js & react-chartjs-2 (Visualizations)
- Vite (Build tool)

## 📋 Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher
- **npm**: 8.x or higher
- **PostgreSQL**: 14.x or higher (optional, SQLite is default)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Drone Flight Telemetry log analyzer"
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env
# Edit .env and configure your database URL
```

**Database Configuration:**

For SQLite (default):
```env
DATABASE_URL=sqlite:///./database/drone_telemetry.db
```

For PostgreSQL:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/drone_telemetry
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
copy .env.example .env
# The default API URL should work for local development
```

## 🏃 Running the Application

### Start Backend Server

```bash
cd backend
python run.py
```

The backend API will be available at: `http://localhost:8000`
API documentation (Swagger): `http://localhost:8000/docs`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## 📖 Usage Guide

### 1. Upload Telemetry Data

1. Navigate to the **Upload** page
2. Select a `.bin` or `.tlog` telemetry file
3. Enter a **Drone ID** (e.g., "DRONE-001")
4. Optionally provide a **Drone Name** for easier identification
5. Enable **Run predictive analytics** to automatically analyze the flight
6. Click **Upload and Process**

### 2. View Drone Fleet

- Navigate to **Drones** to see all registered drones
- Click on a drone to view detailed information, trends, and alerts

### 3. Analyze Flight Data

- Navigate to **Flights** to see all recorded flights
- Click on a flight to view detailed telemetry metrics:
  - Motor PWM outputs
  - Battery health metrics
  - Vibration analysis
  - Flight performance data

### 4. Monitor Maintenance Alerts

- Navigate to **Maintenance** to see all alerts
- Filter by severity (Critical, Warning, Info) or status (Resolved/Unresolved)
- Review recommendations for each alert
- Acknowledge or resolve alerts as maintenance is performed

### 5. Dashboard Overview

The dashboard provides:
- Fleet statistics (total drones, flights, alerts)
- Recent flight activity
- Unresolved maintenance alerts
- Quick access to drone health status

## 🔧 Configuration

### Backend Configuration (`backend/.env`)

```env
# Database
DATABASE_URL=sqlite:///./database/drone_telemetry.db

# Application
APP_NAME=Drone Telemetry Parser
APP_VERSION=1.0.0
DEBUG=True

# Predictive Maintenance Thresholds (percentage deviation)
MOTOR_PWM_THRESHOLD_PERCENT=15.0
BATTERY_VOLTAGE_THRESHOLD_PERCENT=10.0
VIBRATION_THRESHOLD_PERCENT=20.0

# Rolling window for baseline calculation
ROLLING_WINDOW_FLIGHTS=5

# Upload Settings
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes
```

### Adjusting Alert Thresholds

Modify these values to make alerts more or less sensitive:
- **Lower values**: More sensitive, generate more alerts
- **Higher values**: Less sensitive, only flag significant deviations

Example for sensitive monitoring:
```env
MOTOR_PWM_THRESHOLD_PERCENT=10.0
BATTERY_VOLTAGE_THRESHOLD_PERCENT=5.0
VIBRATION_THRESHOLD_PERCENT=15.0
```

## 📊 API Endpoints

### Telemetry
- `POST /api/telemetry/upload` - Upload and process telemetry file
- `GET /api/telemetry/validate-file/{filename}` - Validate file type

### Drones
- `GET /api/drones/` - List all drones
- `GET /api/drones/{id}` - Get drone details
- `GET /api/drones/{id}/health` - Get drone health summary
- `PUT /api/drones/{id}` - Update drone information
- `DELETE /api/drones/{id}` - Delete drone

### Flights
- `GET /api/flights/` - List flights
- `GET /api/flights/{id}` - Get flight details
- `GET /api/flights/{id}/telemetry` - Get flight telemetry data
- `DELETE /api/flights/{id}` - Delete flight

### Analytics
- `POST /api/analytics/analyze/{flight_id}` - Run analytics on flight
- `GET /api/analytics/trends/motors/{drone_id}` - Get motor trends
- `GET /api/analytics/trends/battery/{drone_id}` - Get battery trends
- `GET /api/analytics/trends/vibration/{drone_id}` - Get vibration trends
- `GET /api/analytics/compare/{drone_id}` - Compare two flights
- `GET /api/analytics/statistics/{drone_id}` - Get drone statistics

### Maintenance
- `GET /api/maintenance/` - List maintenance alerts
- `GET /api/maintenance/{id}` - Get alert details
- `PATCH /api/maintenance/{id}/acknowledge` - Acknowledge alert
- `PATCH /api/maintenance/{id}/resolve` - Resolve alert
- `DELETE /api/maintenance/{id}` - Delete alert

## 🧪 Testing

### Backend Testing

```bash
cd backend
pytest
```

### Frontend Testing

```bash
cd frontend
npm run test
```

## 📦 Production Build

### Backend

```bash
cd backend
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm run build
# Serve the dist/ directory with your web server
```

## 🐛 Troubleshooting

### Database Connection Issues

**SQLite:**
- Ensure the `backend/database/` directory exists
- Check file permissions

**PostgreSQL:**
- Verify PostgreSQL service is running
- Check connection credentials in `.env`
- Ensure database exists: `createdb drone_telemetry`

### File Upload Issues

- Verify file size is under 100MB
- Ensure file extension is `.bin` or `.tlog`
- Check backend logs for parsing errors
- Validate MAVLink message format

### Parser Errors

If telemetry parsing fails:
1. Verify the file is a valid MAVLink log
2. Check for corrupt data in the file
3. Review backend logs for specific error messages
4. Try with a known-good telemetry file

### Frontend Not Connecting

- Verify backend is running on port 8000
- Check CORS configuration in `backend/app/main.py`
- Ensure frontend proxy is configured in `vite.config.js`

## 🔒 Security Considerations

- **File Upload**: Files are validated for type and size
- **SQL Injection**: SQLAlchemy ORM provides protection
- **CORS**: Configure allowed origins in production
- **Authentication**: Add JWT/OAuth for production use (not included)

## 📈 Performance Optimization

- **Database Indexing**: Key fields are indexed for fast queries
- **Rolling Window**: Configurable to balance accuracy vs performance
- **File Processing**: Async processing recommended for large files
- **Frontend**: Code splitting and lazy loading implemented

## 🛠️ Development

### Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Telemetry parser
│   │   ├── database.py      # Database configuration
│   │   └── main.py          # FastAPI application
│   ├── uploads/             # Uploaded telemetry files
│   ├── database/            # SQLite database
│   ├── config.py            # Configuration settings
│   ├── requirements.txt     # Python dependencies
│   └── run.py               # Server entry point
│
└── frontend/
    ├── src/
    │   ├── components/      # Reusable components
    │   ├── pages/           # Page components
    │   ├── services/        # API client
    │   ├── utils/           # Helper functions
    │   ├── styles/          # CSS styles
    │   ├── App.jsx          # Main application
    │   └── main.jsx         # Entry point
    ├── public/              # Static assets
    ├── index.html           # HTML template
    ├── package.json         # Node dependencies
    └── vite.config.js       # Vite configuration
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

Developed as a comprehensive drone fleet management and predictive maintenance solution.

## 🙏 Acknowledgments

- **pymavlink**: MAVLink protocol implementation
- **FastAPI**: Modern web framework for building APIs
- **Chart.js**: Beautiful, responsive charts
- **React**: UI library for building interfaces

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the troubleshooting section

---

**Built with ❤️ for drone operators and maintenance teams**
