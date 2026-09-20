from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import SkillVerificationStatus
from app.services.demo_seed import seed_demo_data
from app.services.verification_engine import compute_skill_status


def test_demo_seeding_and_john_doe_states(db_session):
    """
    Verify complete demo seeding:
    - John Doe exists with CGPA 8.2, B.Tech CSE
    - Coordinator exists
    - Four MVP skills exist
    - Exact required skill states for John Doe
    """
    result = seed_demo_data(db_session, force_reset=True)
    assert result["status"] == "success"

    # Verify Coordinator
    coordinator = db_session.query(User).filter(User.email == "coordinator@college.edu").first()
    assert coordinator is not None
    assert coordinator.role == UserRole.PLACEMENT_COORDINATOR

    # Verify Skills
    skills = db_session.query(Skill).all()
    assert len(skills) == 4
    skill_names = {s.name for s in skills}
    assert skill_names == {"Python", "Pandas", "Matplotlib", "Git/GitHub"}

    # Verify John Doe Profile
    john_user = db_session.query(User).filter(User.email == "john.doe@nit.edu").first()
    assert john_user is not None
    assert john_user.role == UserRole.STUDENT

    john_profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == john_user.id).first()
    assert john_profile is not None
    assert john_profile.full_name == "John Doe"
    assert john_profile.qualification == "B.Tech"
    assert john_profile.branch == "CSE"
    assert john_profile.academic_year == 2026
    assert john_profile.cgpa == 8.2

    # Verify John Doe Skill States
    expected_states = {
        "Python": SkillVerificationStatus.SKILL_VERIFIED,
        "Pandas": SkillVerificationStatus.SKILL_ASSESSED,
        "Matplotlib": SkillVerificationStatus.EVIDENCE_SUPPORTED,
        "Git/GitHub": SkillVerificationStatus.EVIDENCE_SUPPORTED,
    }

    for skill in skills:
        student_skill = [ss for ss in john_profile.skills if ss.skill_id == skill.id][0]
        assert student_skill.verification_status == expected_states[skill.name]

        # In addition, check that compute_skill_status deterministically matches!
        computed = compute_skill_status(john_profile.id, skill.id, db_session)
        assert computed == expected_states[skill.name]


def test_demo_api_endpoints(client, db_session):
    """Test /api/v1/demo/status and /api/v1/demo/reset endpoints."""
    seed_demo_data(db_session, force_reset=True)

    status_res = client.get("/api/v1/demo/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["demo_mode"] is True
    assert status_data["total_students"] == 4
    assert status_data["coordinator_account"] == "coordinator@college.edu"

    # Reset endpoint
    reset_res = client.post("/api/v1/demo/reset")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert "successfully reset" in reset_data["message"]
