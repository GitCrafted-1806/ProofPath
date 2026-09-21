from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

def create_db_engine(db_url: str = None):
    url = db_url or settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    connect_args = {}
    engine_kwargs = {"echo": False}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL / Production database configuration
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20

    return create_engine(url, **engine_kwargs)


engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """Initialize database schemas and create tables."""
    eng = target_engine or engine
    # Import all models so metadata is populated before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=eng)

    # Safe SQLite column migration for development environments
    db_url = str(eng.url) if hasattr(eng, "url") else settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        with eng.connect() as conn:
            cursor = conn.exec_driver_sql("PRAGMA table_info(assessments)")
            cols = [row[1] for row in cursor.fetchall()]
            if cols:
                if "questions" not in cols:
                    conn.exec_driver_sql("ALTER TABLE assessments ADD COLUMN questions JSON DEFAULT '[]' NOT NULL")
                if "submission" not in cols:
                    conn.exec_driver_sql("ALTER TABLE assessments ADD COLUMN submission JSON DEFAULT '{}'")
            conn.commit()
