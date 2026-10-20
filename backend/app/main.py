from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from app.database import init_db
import os

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Drone Telemetry Parser and Predictive Maintenance System"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"[DIR]   Upload directory: {settings.UPLOAD_DIR}")
    print(f"[DB]    Database: {settings.DATABASE_URL}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers (will be created next)
from app.routers import telemetry, drones, flights, analytics, maintenance, components

app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(drones.router, prefix="/api/drones", tags=["drones"])
app.include_router(flights.router, prefix="/api/flights", tags=["flights"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["maintenance"])
app.include_router(components.router, prefix="/api/components", tags=["components"])
