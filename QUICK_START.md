# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

Ensure you have installed:
- ✅ Python 3.9+
- ✅ Node.js 16+
- ✅ npm 8+

Verify with:
```bash
python --version
node --version
npm --version
```

## Installation (5 Steps)

### 1. Clone & Navigate
```bash
git clone <repository-url>
cd "Drone Flight Telemetry log analyzer"
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

### 4. Start Backend (Terminal 1)
```bash
cd backend
python run.py
```
✅ Backend running at: http://localhost:8000

### 5. Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
✅ Frontend running at: http://localhost:3000

## First Upload

1. Open http://localhost:3000/upload
2. Select a `.bin` or `.tlog` file from your drone
3. Enter Drone ID (e.g., "DRONE-001")
4. Click **Upload and Process**
5. View results in Flights or Drones pages

## Quick Navigation

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | http://localhost:3000 | Overview & stats |
| Drones | http://localhost:3000/drones | Fleet management |
| Flights | http://localhost:3000/flights | Flight history |
| Maintenance | http://localhost:3000/maintenance | Alerts & warnings |
| Upload | http://localhost:3000/upload | Upload telemetry |
| API Docs | http://localhost:8000/docs | API reference |

## Common Issues

**Backend won't start?**
```bash
# Check if port 8000 is in use
# Kill and restart
```

**Frontend won't start?**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Upload fails?**
- Verify file is `.bin` or `.tlog`
- Check file size < 100MB
- Ensure backend is running

## Default Configuration

The system works out-of-the-box with:
- **Database**: SQLite (no setup needed)
- **Port**: Backend on 8000, Frontend on 3000
- **Alert Thresholds**: 
  - Motor: 15% deviation
  - Battery: 10% deviation
  - Vibration: 20% deviation
- **Rolling Window**: 5 previous flights

## Next Steps

- 📖 Read [README.md](README.md) for full documentation
- 🔧 See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- 🌐 Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details

## Test the System

### 1. Upload Test Data
Upload a sample telemetry file with drone ID "TEST-001"

### 2. Check Dashboard
View the dashboard to see your drone and flight stats

### 3. View Trends
Click on the drone to see motor, battery, and vibration trends

### 4. Monitor Alerts
Check the Maintenance page for any predictive warnings

## File Locations

```
├── backend/
│   ├── database/          # SQLite database file (auto-created)
│   ├── uploads/           # Uploaded telemetry files
│   └── .env              # Configuration (copy from .env.example)
│
└── frontend/
    └── .env              # Frontend config (copy from .env.example)
```

## Useful Commands

### Backend
```bash
# Start server
python run.py

# Check API
curl http://localhost:8000/health
```

### Frontend
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Getting Help

1. Check the [troubleshooting section](SETUP_GUIDE.md#troubleshooting)
2. Review backend console logs
3. Check browser console (F12) for frontend errors
4. Verify all prerequisites are installed

---

**You're all set! Start analyzing your drone telemetry data.** 🚁
