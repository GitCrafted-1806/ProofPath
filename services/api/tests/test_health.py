from sqlalchemy import inspect
from app.models.skill import Skill, MVP_SKILLS


def test_api_health(client):
    """Verify the /api/health endpoint responds with healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ProofPath API"
    assert "version" in data


def test_database_tables_exist(db_session):
    """Verify all required SQLAlchemy database tables exist."""
    inspector = inspect(db_session.bind)
    table_names = inspector.get_table_names()

    required_tables = [
        "users",
        "student_profiles",
        "skills",
        "student_skills",
        "evidence",
        "assessments",
        "placement_requirements",
        "audit_logs"
    ]

    for table in required_tables:
        assert table in table_names, f"Missing table: {table}"


def test_mvp_skills_seeded(db_session):
    """Verify that exactly the 4 MVP skills are present in the database."""
    skills = db_session.query(Skill).all()
    skill_names = [s.name for s in skills]

    assert len(skills) == 4
    for expected_skill in MVP_SKILLS:
        assert expected_skill in skill_names
