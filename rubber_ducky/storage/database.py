"""SQLAlchemy database setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

Base = declarative_base()

# Default database instance (created lazily)
_default_db = None


def get_database(database_path: Path = None):
    """Get or create the default database instance.

    Args:
        database_path: Path to SQLite database file (uses config default if None)

    Returns:
        Database instance
    """
    global _default_db

    if _default_db is None:
        if database_path is None:
            from rubber_ducky.config import settings
            database_path = settings.database_path

        _default_db = Database(database_path)

    return _default_db


def _get_session_local():
    """Get SessionLocal (lazy initialization)."""
    db = get_database()
    return db.SessionLocal


# Create a lazy SessionLocal that initializes database on first call
class _LazySessionLocal:
    """Lazy sessionmaker that initializes database on first call."""

    def __init__(self):
        self._session_maker = None

    def __call__(self):
        """Create a new session."""
        if self._session_maker is None:
            db = get_database()
            db.create_tables()  # Ensure tables exist
            self._session_maker = db.SessionLocal
        return self._session_maker()


# Export SessionLocal as a callable
SessionLocal = _LazySessionLocal()


class Database:
    """Database connection and session manager."""

    def __init__(self, database_path: Path):
        """Initialize database connection.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
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
