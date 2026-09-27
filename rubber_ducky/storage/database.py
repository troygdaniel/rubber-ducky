"""SQLAlchemy database setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

Base = declarative_base()


class Database:
    """Database connection and session manager."""

    def __init__(self, database_path: Path):
        """Initialize database connection.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
