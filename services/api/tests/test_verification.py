import uuid
from datetime import datetime, timezone
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.assessment import Assessment
from app.models.student_skill import SkillVerificationStatus, StudentSkill
from app.services.verification_engine import compute_skill_status, update_and_persist_skill_status


def setup_student_and_skill(db_session, skill_name="Python"):
    """Helper to create a student user and retrieve the requested skill."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT
    )
    db_session.add(user)
    db_session.flush()

    profile = StudentProfile(
        user_id=user.id,
        full_name="Verification Tester",
        qualification="B.Tech",
        college_name="Test College",
        branch="CSE",
        academic_year=2026,
        cgpa=8.0
    )
    db_session.add(profile)
    db_session.flush()

    skill = db_session.query(Skill).filter(Skill.name == skill_name).first()
    student_skill = StudentSkill(
        student_id=profile.id,
        skill_id=skill.id,
        verification_status=SkillVerificationStatus.UNVERIFIED
    )
    db_session.add(student_skill)
    db_session.commit()

    return profile, skill, student_skill


def test_transition_no_evidence_is_unverified(db_session):
    """Test Rule 1: Student without evidence has UNVERIFIED status."""
    profile, skill, _ = setup_student_and_skill(db_session)
    status = compute_skill_status(profile.id, skill.id, db_session)
    assert status == SkillVerificationStatus.UNVERIFIED


def test_transition_evidence_only_is_evidence_supported(db_session):
    """Test Rule 2: Uploaded certificate moves skill to EVIDENCE_SUPPORTED."""
    profile, skill, _ = setup_student_and_skill(db_session)

    # Add certificate evidence
    evidence = Evidence(
        student_id=profile.id,
        type=EvidenceType.CERTIFICATE,
        file_path="/cert/py.pdf",
        authenticity_state=AuthenticityState.SUBMITTED,
        mapped_skills=[skill.name]
    )
    db_session.add(evidence)
    db_session.commit()

    status = compute_skill_status(profile.id, skill.id, db_session)
    assert status == SkillVerificationStatus.EVIDENCE_SUPPORTED


def test_transition_evidence_plus_passed_assessment_is_skill_assessed(db_session):
    """Test Rule 3: Evidence + passed practical assessment moves skill to SKILL_ASSESSED."""
    profile, skill, _ = setup_student_and_skill(db_session)

    evidence = Evidence(
        student_id=profile.id,
        type=EvidenceType.CERTIFICATE,
        file_path="/cert/py.pdf",
        authenticity_state=AuthenticityState.SOURCE_SUPPORTED,
        mapped_skills=[skill.name]
    )
    db_session.add(evidence)

    assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="PRACTICAL",
        status="COMPLETED",
        score=85.0,
        passed=True,
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(assessment)
    db_session.commit()

    status = compute_skill_status(profile.id, skill.id, db_session)
    assert status == SkillVerificationStatus.SKILL_ASSESSED


def test_transition_all_criteria_is_skill_verified(db_session):
    """Test Rule 4: Evidence + Assessment + GitHub repo + Follow-up check produces SKILL_VERIFIED."""
    profile, skill, student_skill = setup_student_and_skill(db_session)

    # 1. Supporting evidence
    evidence = Evidence(
        student_id=profile.id,
        type=EvidenceType.CERTIFICATE,
        file_path="/cert/py.pdf",
        authenticity_state=AuthenticityState.SOURCE_SUPPORTED,
        mapped_skills=[skill.name]
    )
    db_session.add(evidence)

    # 2. Practical assessment passed
    prac_assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="PRACTICAL",
        status="COMPLETED",
        score=90.0,
        passed=True,
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(prac_assessment)

    # 3. GitHub repository project evidence
    github_evidence = Evidence(
        student_id=profile.id,
        type=EvidenceType.GITHUB_REPO,
        file_path="https://github.com/student/py-engine",
        authenticity_state=AuthenticityState.SOURCE_SUPPORTED,
        mapped_skills=[skill.name]
    )
    db_session.add(github_evidence)

    # 4. Follow-up understanding check passed
    followup_assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="FOLLOW_UP",
        status="COMPLETED",
        score=95.0,
        passed=True,
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(followup_assessment)
    db_session.commit()

    status = compute_skill_status(profile.id, skill.id, db_session)
    assert status == SkillVerificationStatus.SKILL_VERIFIED

    # Test persistence and audit logging
    updated = update_and_persist_skill_status(profile.id, skill.id, db_session)
    assert updated.verification_status == SkillVerificationStatus.SKILL_VERIFIED


def test_incomplete_conditions_do_not_produce_skill_verified(db_session):
    """
    Test negative cases: incomplete conditions MUST NOT produce SKILL_VERIFIED.
    """
    profile, skill, _ = setup_student_and_skill(db_session)

    # Condition A: Has GitHub + Assessment + Follow-up, but NO supporting evidence
    # Must remain UNVERIFIED because baseline evidence is absent
    github = Evidence(
        student_id=profile.id,
        type=EvidenceType.GITHUB_REPO,
        file_path="https://github.com/student/repo",
        mapped_skills=[skill.name]
    )
    assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="PRACTICAL",
        passed=True
    )
    followup = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="FOLLOW_UP",
        passed=True
    )
    db_session.add_all([github, assessment, followup])
    db_session.commit()

    status_no_cert = compute_skill_status(profile.id, skill.id, db_session)
    assert status_no_cert == SkillVerificationStatus.UNVERIFIED

    # Condition B: Now add certificate, but remove follow-up
    # Supporting evidence + GitHub + Assessment, but NO follow-up
    cert = Evidence(
        student_id=profile.id,
        type=EvidenceType.CERTIFICATE,
        mapped_skills=[skill.name]
    )
    db_session.add(cert)
    db_session.delete(followup)
    db_session.commit()

    status_no_followup = compute_skill_status(profile.id, skill.id, db_session)
    assert status_no_followup == SkillVerificationStatus.SKILL_ASSESSED
    assert status_no_followup != SkillVerificationStatus.SKILL_VERIFIED

    # Condition C: Supporting evidence + Assessment + Follow-up, but NO GitHub repo
    db_session.delete(github)
    followup2 = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type="FOLLOW_UP",
        passed=True
    )
    db_session.add(followup2)
    db_session.commit()

    status_no_github = compute_skill_status(profile.id, skill.id, db_session)
    assert status_no_github == SkillVerificationStatus.SKILL_ASSESSED
    assert status_no_github != SkillVerificationStatus.SKILL_VERIFIED
