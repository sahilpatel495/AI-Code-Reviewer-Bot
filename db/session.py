"""
Database Session Management

This module handles database connections and session management for the AI Code Reviewer Bot.
"""

from contextlib import contextmanager
from typing import Generator

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config.settings import settings
from db.models import Base

logger = structlog.get_logger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=settings.debug  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


def drop_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.
    
    This context manager ensures that database sessions are properly
    closed and transactions are committed or rolled back as needed.
    
    Usage:
        with get_db_session() as session:
            # Use session here
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        session.close()


def get_db_session_dependency() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.
    
    This function is used as a dependency in FastAPI endpoints to
    automatically manage database sessions.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def test_database_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with get_db_session() as session:
            # Execute a simple query to test connection
            result = session.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


async def get_database_info() -> dict:
    """
    Get database information and statistics.
    
    Returns:
        Dictionary containing database information
    """
    try:
        with get_db_session() as session:
            # Get database version
            version_result = session.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]
            
            # Get database size
            size_result = session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
            size = size_result.fetchone()[0]
            
            # Get connection count
            conn_result = session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"))
            connections = conn_result.fetchone()[0]
            
            # Get table counts
            table_counts = {}
            for table in Base.metadata.tables.keys():
                try:
                    count_result = session.execute(text(f"SELECT count(*) FROM {table}"))
                    table_counts[table] = count_result.fetchone()[0]
                except Exception:
                    table_counts[table] = 0
            
            return {
                "version": version,
                "size": size,
                "connections": connections,
                "table_counts": table_counts,
                "status": "healthy"
            }
            
    except Exception as e:
        logger.error("Failed to get database info", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


async def cleanup_old_data(days_to_keep: int = 30):
    """
    Clean up old data from the database.
    
    Args:
        days_to_keep: Number of days of data to keep
    """
    try:
        with get_db_session() as session:
            # Clean up old webhook events
            webhook_cleanup = session.execute(
                text("""
                    DELETE FROM webhook_events 
                    WHERE received_at < NOW() - INTERVAL :days DAY
                """),
                {"days": days_to_keep}
            )
            webhook_deleted = webhook_cleanup.rowcount
            
            # Clean up old system metrics
            metrics_cleanup = session.execute(
                text("""
                    DELETE FROM system_metrics 
                    WHERE recorded_at < NOW() - INTERVAL :days DAY
                """),
                {"days": days_to_keep}
            )
            metrics_deleted = metrics_cleanup.rowcount
            
            # Clean up old rate limit records
            rate_limit_cleanup = session.execute(
                text("""
                    DELETE FROM rate_limits 
                    WHERE updated_at < NOW() - INTERVAL :days DAY
                """),
                {"days": days_to_keep}
            )
            rate_limit_deleted = rate_limit_cleanup.rowcount
            
            logger.info(
                "Database cleanup completed",
                webhook_events_deleted=webhook_deleted,
                system_metrics_deleted=metrics_deleted,
                rate_limits_deleted=rate_limit_deleted,
                days_kept=days_to_keep
            )
            
    except Exception as e:
        logger.error("Database cleanup failed", error=str(e))
        raise


async def get_database_health() -> dict:
    """
    Get database health information.
    
    Returns:
        Dictionary containing database health metrics
    """
    try:
        with get_db_session() as session:
            # Check connection pool status
            pool_status = {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
            
            # Check for long-running queries
            long_queries = session.execute(text("""
                SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
                FROM pg_stat_activity 
                WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                AND state = 'active'
            """)).fetchall()
            
            # Check for locks
            locks = session.execute(text("""
                SELECT count(*) as lock_count
                FROM pg_locks 
                WHERE NOT granted
            """)).fetchone()
            
            return {
                "status": "healthy",
                "pool_status": pool_status,
                "long_running_queries": len(long_queries),
                "blocked_queries": locks[0] if locks else 0,
                "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
            }
            
    except Exception as e:
        logger.error("Failed to get database health", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Initialize database on module import
try:
    create_tables()
    logger.info("Database initialization completed")
except Exception as e:
    logger.error("Database initialization failed", error=str(e))
    raise
