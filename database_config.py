"""
Database configuration and session management.

This module provides database connection setup and session factory
for the Flash Loan Safety Net application.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from database_models import Base


# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./flash_loan_safety.db"
)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL logging
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_database() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Use as dependency injection in FastAPI:
    
    @app.get("/transactions")
    def get_transactions(db: Session = Depends(get_db)):
        return db.query(Transaction).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import (for development)
if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database ready!")
