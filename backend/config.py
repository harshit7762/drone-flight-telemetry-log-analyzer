from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./database/drone_telemetry.db"
    
    # Application
    APP_NAME: str = "Drone Telemetry Parser"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Predictive Maintenance Thresholds
    MOTOR_PWM_THRESHOLD_PERCENT: float = 15.0
    BATTERY_VOLTAGE_THRESHOLD_PERCENT: float = 10.0
    # Battery Internal Resistance (mΩ)
    # Alert when average internal resistance rises by this percentage above baseline
    BATTERY_RESISTANCE_THRESHOLD_PERCENT: float = 25.0
    # Absolute warning threshold for overall pack resistance (mΩ)
    BATTERY_RESISTANCE_MAX_ABSOLUTE_MOHM: float = 60.0
    VIBRATION_THRESHOLD_PERCENT: float = 20.0
    # Absolute minimum vibration floor (m/s²). Vibrations below this are considered
    # negligible background noise in flight controllers and will not trigger false alarms.
    VIBRATION_MIN_FLOOR_ABS: float = 1.0
    ROLLING_WINDOW_FLIGHTS: int = 5

    # GPS Signal Loss
    # Alert when fix ratio drops below this value vs historical baseline.
    # e.g. 0.80 means: alert if GPS had a lock < 80% of the flight
    GPS_FIX_RATIO_MIN_ABSOLUTE: float = 0.80   # alert below 80% fix in any flight
    GPS_FIX_RATIO_THRESHOLD_PERCENT: float = 15.0  # or alert if 15% worse than baseline

    # Temperature Spikes
    # Alert when avg temperature exceeds baseline by this many degrees Celsius
    TEMPERATURE_AVG_THRESHOLD_CELSIUS: float = 15.0
    # Alert when max temperature exceeds this absolute value (regardless of baseline)
    TEMPERATURE_MAX_ABSOLUTE_CELSIUS: float = 80.0
    # Alert when spike count exceeds this many readings above 2-sigma
    TEMPERATURE_SPIKE_COUNT_THRESHOLD: int = 10
    
    # Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
