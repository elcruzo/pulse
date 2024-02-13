"""
Database configuration and connection management
"""

import databases
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = settings.DATABASE_URL

# SQLAlchemy setup
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

# Databases async interface
database = databases.Database(DATABASE_URL)

async def init_db():
    """Initialize database connection"""
    try:
        await database.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

async def close_db():
    """Close database connection"""
    try:
        await database.disconnect()
        logger.info("Database disconnected successfully")
    except Exception as e:
        logger.error(f"Error disconnecting database: {e}")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()