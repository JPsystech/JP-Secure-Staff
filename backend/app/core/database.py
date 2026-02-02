import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

# FIXED: Add connection pool settings for stability
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,        # Connection pool size
    max_overflow=20      # Max overflow connections
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Database session dependency. Logs only real DB errors; lets HTTPException (e.g. 401) propagate.
    """
    db = SessionLocal()
    try:
        yield db
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        db.rollback()
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

