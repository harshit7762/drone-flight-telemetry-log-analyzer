from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and run lightweight migrations for new columns"""
    Base.metadata.create_all(bind=engine)
    
    # Check for missing columns in telemetry_summaries and add them if needed
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        existing_cols = {col['name'] for col in inspector.get_columns("telemetry_summaries")}
        
        new_columns = [
            ("battery_internal_resistance_avg", "FLOAT"),
            ("battery_internal_resistance_min", "FLOAT"),
            ("battery_internal_resistance_max", "FLOAT"),
        ]
        
        with engine.begin() as conn:
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE telemetry_summaries ADD COLUMN {col_name} {col_type};"))
    except Exception as e:
        print(f"[DB] Migration check notice: {e}")

