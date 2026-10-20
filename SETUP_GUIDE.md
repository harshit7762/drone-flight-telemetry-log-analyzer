# Complete Setup Guide

This guide provides detailed step-by-step instructions for setting up the Drone Telemetry Parser and Predictive Maintenance System.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installing Prerequisites](#installing-prerequisites)
3. [Database Setup](#database-setup)
4. [Backend Installation](#backend-installation)
5. [Frontend Installation](#frontend-installation)
6. [Running the Application](#running-the-application)
7. [Initial Configuration](#initial-configuration)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

### Software Requirements
- Python 3.9 or higher
- Node.js 16.x or higher
- npm 8.x or higher
- Git (for cloning repository)
- PostgreSQL 14+ (optional, SQLite is default)

## Installing Prerequisites

### Windows

#### Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer and check "Add Python to PATH"
3. Verify installation:
   ```powershell
   python --version
   ```

#### Install Node.js
1. Download from [nodejs.org](https://nodejs.org/)
2. Run installer (includes npm)
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

#### Install PostgreSQL (Optional)
1. Download from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run installer, set password for postgres user
3. Note the port (default: 5432)

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.9

# Install Node.js
brew install node

# Install PostgreSQL (optional)
brew install postgresql@14
brew services start postgresql@14
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python
sudo apt install python3.9 python3.9-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs

# Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Database Setup

### Option 1: SQLite (Recommended for Development)

SQLite requires no additional setup. The database file will be created automatically on first run.

### Option 2: PostgreSQL (Recommended for Production)

#### Create Database

**Windows:**
```powershell
# Open PowerShell and connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE drone_telemetry;
CREATE USER drone_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE drone_telemetry TO drone_user;
\q
```

**macOS/Linux:**
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE drone_telemetry;
CREATE USER drone_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE drone_telemetry TO drone_user;
\q
```

## Backend Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd "Drone Flight Telemetry log analyzer"
```

### Step 2: Set Up Virtual Environment

**Windows:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI
- uvicorn
- SQLAlchemy
- pymavlink
- NumPy, Pandas
- And other dependencies

### Step 4: Configure Environment

```bash
# Copy example environment file
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env
```

Edit `.env` file:

**For SQLite:**
```env
DATABASE_URL=sqlite:///./database/drone_telemetry.db
DEBUG=True
```

**For PostgreSQL:**
```env
DATABASE_URL=postgresql://drone_user:your_secure_password@localhost:5432/drone_telemetry
DEBUG=True
```

### Step 5: Create Required Directories

```bash
# Windows:
mkdir database uploads

# macOS/Linux:
mkdir -p database uploads
```

### Step 6: Initialize Database

The database tables will be created automatically when you first run the application.

## Frontend Installation

### Step 1: Navigate to Frontend Directory

```bash
cd ../frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

This will install:
- React and React Router
- Axios
- Chart.js
- Vite
- And other dependencies

### Step 3: Configure Environment

```bash
# Copy example environment file
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env
```

The default configuration should work:
```env
VITE_API_URL=http://localhost:8000/api
```

## Running the Application

### Start Backend Server

**Terminal 1:**
```bash
cd backend

# Activate virtual environment (if not already active)
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start server
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify Backend:**
- Open browser: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Start Frontend Server

**Terminal 2:**
```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.0.11  ready in 500 ms
➜  Local:   http://localhost:3000/
```

**Verify Frontend:**
- Open browser: http://localhost:3000
- You should see the dashboard

## Initial Configuration

### 1. Verify System is Running

1. Open http://localhost:3000
2. You should see the dashboard with navigation
3. All pages should load without errors

### 2. Adjust Alert Thresholds (Optional)

Edit `backend/.env`:

```env
# Make alerts more sensitive (detect smaller changes)
MOTOR_PWM_THRESHOLD_PERCENT=10.0
BATTERY_VOLTAGE_THRESHOLD_PERCENT=5.0
VIBRATION_THRESHOLD_PERCENT=15.0

# Make alerts less sensitive (only major issues)
MOTOR_PWM_THRESHOLD_PERCENT=20.0
BATTERY_VOLTAGE_THRESHOLD_PERCENT=15.0
VIBRATION_THRESHOLD_THRESHOLD_PERCENT=25.0
```

Restart backend after changes.

### 3. Set Rolling Window

Adjust how many previous flights to use for baseline:

```env
ROLLING_WINDOW_FLIGHTS=5  # Use last 5 flights
```

### 4. Test with Sample Data

1. Get a sample .bin or .tlog file from your drone
2. Go to Upload page: http://localhost:3000/upload
3. Upload the file with a drone ID (e.g., "TEST-001")
4. Wait for processing
5. View results in Flights and Drones pages

## Troubleshooting

### Backend Won't Start

**Port Already in Use:**
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

**Module Not Found:**
```bash
# Ensure virtual environment is active
# Reinstall dependencies
pip install -r requirements.txt
```

**Database Connection Error:**
```bash
# For PostgreSQL, verify service is running
# Windows:
services.msc  # Look for PostgreSQL service

# macOS:
brew services list

# Linux:
sudo systemctl status postgresql
```

### Frontend Won't Start

**Port Already in Use:**
```bash
# The frontend will automatically use the next available port
# Or kill the process using port 3000
```

**Dependency Issues:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Build Errors:**
```bash
# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Upload Fails

**File Too Large:**
- Default max: 100MB
- Increase in `backend/.env`: `MAX_UPLOAD_SIZE=209715200` (200MB)

**Parsing Errors:**
- Verify file is valid MAVLink format
- Check backend console for detailed errors
- Try with a known-good telemetry file

### Database Issues

**SQLite Locked:**
```bash
# Close all connections or restart backend
```

**PostgreSQL Authentication:**
```bash
# Edit pg_hba.conf to allow password authentication
# Restart PostgreSQL service
```

**Migration Issues:**
```bash
# Delete database and let it recreate (LOSES DATA)
# For SQLite:
rm backend/database/drone_telemetry.db

# For PostgreSQL:
dropdb drone_telemetry
createdb drone_telemetry
```

## Next Steps

1. **Read the README**: Full feature documentation
2. **Upload Test Data**: Try with sample telemetry files
3. **Configure Alerts**: Adjust thresholds for your use case
4. **Explore API**: Check http://localhost:8000/docs
5. **Deploy to Production**: See production deployment guide

## Getting Help

If you encounter issues:
1. Check this troubleshooting section
2. Review backend logs in terminal
3. Check browser console for frontend errors
4. Verify all prerequisites are installed
5. Ensure ports 3000 and 8000 are available

---

**Setup complete! You're ready to start analyzing drone telemetry data.**
