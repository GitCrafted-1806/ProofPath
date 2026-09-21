from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database schemas and create tables."""
    # Import all models so metadata is populated before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safe SQLite column migration for development environments
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            cursor = conn.exec_driver_sql("PRAGMA table_info(assessments)")
            cols = [row[1] for row in cursor.fetchall()]
            if cols:
                if "questions" not in cols:
                    conn.exec_driver_sql("ALTER TABLE assessments ADD COLUMN questions JSON DEFAULT '[]' NOT NULL")
                if "submission" not in cols:
                    conn.exec_driver_sql("ALTER TABLE assessments ADD COLUMN submission JSON DEFAULT '{}'")
            conn.commit()
