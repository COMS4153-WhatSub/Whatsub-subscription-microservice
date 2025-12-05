from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.utils.settings import get_settings
from app.services.orm_models import Base


def get_engine():
    settings = get_settings()
    if not all([settings.db_host, settings.db_user, settings.db_pass, settings.db_name]):
        raise RuntimeError("Database configuration is incomplete. Check db_host, db_user, db_pass, db_name")
    
    # Build MySQL connection URL
    # Cloud SQL connector will handle SSL/TLS authentication
    database_url = f"mysql+pymysql://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    
    # SQLAlchemy 2.0 engine with connection pooling
    # Add connection timeout settings for Cloud Run
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        pool_timeout=20,  # Timeout for getting connection from pool
        connect_args={
            "connect_timeout": 10,  # Connection timeout in seconds
            "read_timeout": 10,  # Read timeout in seconds
            "write_timeout": 10,  # Write timeout in seconds
        },
    )
    return engine


def create_all(engine) -> None:
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)


def get_session_factory() -> sessionmaker[Session]:
    """Get a session factory for database operations."""
    engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

