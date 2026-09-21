"""
Phase 7 Tests: Production Database Configuration and Environment Hardening.
Tests:
- DATABASE_URL environment support (fallback to SQLite, PostgreSQL support)
- postgres:// to postgresql:// scheme normalization (Supabase compatibility)
- PostgreSQL engine pool settings (pool_pre_ping, pool_size, max_overflow)
- PostgreSQL DDL schema compilation for all 9 ProofPath tables
- SECRET_KEY and JWT_SECRET synchronization
- CORS_ORIGINS parsing from string and list
- DEMO_MODE configuration
- Continued SQLite local development operation
"""

import pytest
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from app.core.config import Settings
from app.core.database import create_db_engine, init_db, Base
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill
from app.models.evidence import Evidence
from app.models.assessment import Assessment
from app.models.github_account import GitHubAccount
from app.models.placement_requirement import PlacementRequirement
from app.models.audit_log import AuditLog


def test_database_url_default_fallback_to_sqlite():
    """Verify that when DATABASE_URL is not set or empty, it defaults to SQLite."""
    s = Settings(DATABASE_URL="")
    assert s.DATABASE_URL.startswith("sqlite:///")

    s2 = Settings(DATABASE_URL=None)
    assert s2.DATABASE_URL.startswith("sqlite:///")


def test_database_url_postgres_scheme_normalization():
    """Verify postgres:// (used by Supabase/Heroku) is normalized to postgresql://."""
    supabase_url = "postgres://postgres.abc:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    s = Settings(DATABASE_URL=supabase_url)
    assert s.DATABASE_URL.startswith("postgresql://")
    assert "postgres.abc:mypassword" in s.DATABASE_URL
    assert "supabase.com" in s.DATABASE_URL


def test_database_url_postgresql_direct_scheme():
    """Verify postgresql:// is preserved as-is."""
    pg_url = "postgresql://user:secret@localhost:5432/propath_prod"
    s = Settings(DATABASE_URL=pg_url)
    assert s.DATABASE_URL == pg_url


def test_engine_creation_sqlite_vs_postgres():
    """Verify engine configuration differences: SQLite connect_args vs PostgreSQL pooling."""
    sqlite_eng = create_db_engine("sqlite:///:memory:")
    assert sqlite_eng.dialect.name == "sqlite"

    # For postgresql, verify pooling settings without initiating network connection
    pg_eng = create_db_engine("postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db")
    assert pg_eng.dialect.name == "postgresql"
    assert pg_eng.pool._pre_ping is True
    assert pg_eng.pool.size() == 10
    assert pg_eng.pool._max_overflow == 20


def test_all_models_postgresql_ddl_compilation():
    """
    Verify all 9 ProofPath SQLAlchemy models compile cleanly into valid PostgreSQL DDL
    using SQLAlchemy's PostgreSQL dialect.
    """
    pg_dialect = postgresql.dialect()
    tables = [
        User.__table__,
        StudentProfile.__table__,
        Skill.__table__,
        StudentSkill.__table__,
        Evidence.__table__,
        Assessment.__table__,
        GitHubAccount.__table__,
        PlacementRequirement.__table__,
        AuditLog.__table__,
    ]

    assert len(tables) == 9

    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=pg_dialect))
        assert "CREATE TABLE" in ddl
        assert table.name in ddl
        # Confirm JSON columns compile properly in PostgreSQL
        if "questions" in [c.name for c in table.columns]:
            assert "JSON" in ddl or "json" in ddl.lower()


def test_secret_key_and_jwt_secret_sync():
    """Verify SECRET_KEY configures the JWT secret seamlessly."""
    s = Settings(SECRET_KEY="custom-prod-secret-key-12345")
    assert s.SECRET_KEY == "custom-prod-secret-key-12345"
    assert s.JWT_SECRET == "custom-prod-secret-key-12345"

    s2 = Settings(JWT_SECRET="another-secret-67890")
    assert s2.JWT_SECRET == "another-secret-67890"
    assert s2.SECRET_KEY == "another-secret-67890"


def test_cors_origins_configuration():
    """Verify CORS_ORIGINS parses comma-separated strings and JSON arrays properly."""
    # Comma-separated string
    s1 = Settings(CORS_ORIGINS="https://proofpath.app, https://placement.edu")
    assert s1.CORS_ORIGINS == ["https://proofpath.app", "https://placement.edu"]

    # JSON array string
    s2 = Settings(CORS_ORIGINS='["https://proofpath.app", "https://placement.edu"]')
    assert s2.CORS_ORIGINS == ["https://proofpath.app", "https://placement.edu"]

    # List of strings
    s3 = Settings(CORS_ORIGINS=["https://proofpath.app"])
    assert s3.CORS_ORIGINS == ["https://proofpath.app"]


def test_demo_mode_configuration():
    """Verify DEMO_MODE toggle behavior."""
    s_on = Settings(DEMO_MODE=True)
    assert s_on.DEMO_MODE is True

    s_off = Settings(DEMO_MODE=False)
    assert s_off.DEMO_MODE is False


def test_local_sqlite_initialization_and_operations():
    """Confirm local SQLite database initialization and basic operations still function smoothly."""
    test_eng = create_db_engine("sqlite:///:memory:")
    init_db(target_engine=test_eng)

    # Verify tables created
    insp = test_eng.connect()
    res = insp.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")
    created_tables = {row[0] for row in res.fetchall()}
    insp.close()

    expected_tables = {
        "users", "student_profiles", "skills", "student_skills",
        "evidence", "assessments", "github_accounts", "placement_requirements",
        "audit_logs"
    }
    assert expected_tables.issubset(created_tables)
