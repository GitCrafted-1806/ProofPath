"""Comprehensive test suite for ProofPath Phase 4: Deterministic Assessment & Verification System."""
from datetime import datetime, timezone
import pytest

from app.core.database import Base
from app.models.skill import Skill
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.assessment import Assessment
from app.services.assessment_service import (
    get_assessment_questions,
    mask_questions_for_client,
    evaluate_assessment_submission,
)
from app.services.verification_engine import update_and_persist_skill_status


def register_student(client, email="student_assessment@example.com", name="Assessment Student"):
    """Helper to register and login a student, returning (access_token, profile_id)."""
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": name,
        "cgpa": 8.5
    })
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    profile_id = me.json()["id"]
    return token, profile_id


def register_coordinator(client, email="coord_assessment@example.com"):
    """Helper to register and login a placement coordinator."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "PLACEMENT_COORDINATOR"
    })
    login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return login.json()["access_token"]


def add_supporting_evidence(db_session, profile_id, skill_name="Python"):
    """Helper to seed supporting certificate evidence for a student."""
    ev = Evidence(
        student_id=profile_id,
        type=EvidenceType.CERTIFICATE,
        file_path=f"data/uploads/test_{skill_name.lower()}.pdf",
        original_filename=f"{skill_name}_cert.pdf",
        authenticity_state=AuthenticityState.SUBMITTED,
        extracted_metadata={"issuer": "Coursera", "course_name": f"{skill_name} Mastery"},
        mapped_skills=[skill_name]
    )
    db_session.add(ev)
    db_session.commit()

    skill = db_session.query(Skill).filter(Skill.name == skill_name).first()
    if skill:
        student_skill = db_session.query(StudentSkill).filter(
            StudentSkill.student_id == profile_id,
            StudentSkill.skill_id == skill.id
        ).first()
        if not student_skill:
            student_skill = StudentSkill(
                student_id=profile_id,
                skill_id=skill.id,
                verification_status=SkillVerificationStatus.UNVERIFIED
            )
            db_session.add(student_skill)
            db_session.commit()
        update_and_persist_skill_status(profile_id, skill.id, db_session)
    return ev


def add_github_evidence(db_session, profile_id, skill_name="Python"):
    """Helper to seed GitHub project repository evidence for a student."""
    ev = Evidence(
        student_id=profile_id,
        type=EvidenceType.GITHUB_REPO,
        file_path=f"https://github.com/student/{skill_name.lower()}-project",
        original_filename=f"{skill_name.lower()}-project",
        authenticity_state=AuthenticityState.SUBMITTED,
        extracted_metadata={"repository": f"{skill_name.lower()}-project", "default_branch": "main"},
        mapped_skills=[skill_name]
    )
    db_session.add(ev)
    db_session.commit()

    skill = db_session.query(Skill).filter(Skill.name == skill_name).first()
    if skill:
        student_skill = db_session.query(StudentSkill).filter(
            StudentSkill.student_id == profile_id,
            StudentSkill.skill_id == skill.id
        ).first()
        if not student_skill:
            student_skill = StudentSkill(
                student_id=profile_id,
                skill_id=skill.id,
                verification_status=SkillVerificationStatus.UNVERIFIED
            )
            db_session.add(student_skill)
            db_session.commit()
        update_and_persist_skill_status(profile_id, skill.id, db_session)
    return ev


# --------------------------------------------------------------------------
# Unit Tests for Assessment Service
# --------------------------------------------------------------------------

def test_get_assessment_questions_all_mvp_skills():
    """Verify all 4 MVP skills have both PRACTICAL and FOLLOW_UP questions."""
    for skill in ["Python", "Pandas", "Matplotlib", "Git/GitHub"]:
        practical = get_assessment_questions(skill, "PRACTICAL")
        assert len(practical) >= 3
        for q in practical:
            assert "id" in q
            assert "question" in q
            assert "type" in q
            assert "correct_answer" in q

        followup = get_assessment_questions(skill, "FOLLOW_UP")
        assert len(followup) >= 3
        for q in followup:
            assert "id" in q
            assert "question" in q
            assert "correct_answer" in q


def test_mask_questions_for_client_never_leaks_answers():
    """Verify security masking removes correct_answer and explanation."""
    raw = get_assessment_questions("Python", "PRACTICAL")
    masked = mask_questions_for_client(raw)
    assert len(masked) == len(raw)
    for mq in masked:
        d = mq.model_dump()
        assert "correct_answer" not in d
        assert "explanation" not in d
        assert mq.id
        assert mq.question
        assert mq.type


def test_evaluate_assessment_submission_tolerance_and_logic():
    """Test numeric input float tolerance and string matching in evaluation."""
    questions = [
        {"id": "q1", "type": "MULTIPLE_CHOICE", "correct_answer": "tuple", "points": 1.0, "question": "q1"},
        {"id": "q2", "type": "NUMERICAL_INPUT", "correct_answer": 4, "points": 1.0, "question": "q2"},
        {"id": "q3", "type": "CODE_OUTPUT", "correct_answer": "[2, 6, 10]", "points": 1.0, "question": "q3"},
    ]
    # Correct with whitespace and casing
    answers_pass = {"q1": "  TUPLE  ", "q2": " 4.0000 ", "q3": "[2, 6, 10]"}
    score, passed, feedback, summary = evaluate_assessment_submission(questions, answers_pass)
    assert score == 100.0
    assert passed is True
    assert all(f["is_correct"] for f in feedback)

    # Partial / failing
    answers_fail = {"q1": "list", "q2": "3", "q3": "[2, 6, 10]"}
    score_f, passed_f, feedback_f, summary_f = evaluate_assessment_submission(questions, answers_fail)
    assert score_f == 33.3
    assert passed_f is False
    assert feedback_f[0]["is_correct"] is False


# --------------------------------------------------------------------------
# API Integration Tests
# --------------------------------------------------------------------------

def test_assessment_available_requires_auth(client):
    """GET /available returns 401 without bearer token."""
    res = client.get("/api/v1/assessments/available")
    assert res.status_code == 401


def test_assessment_available_coordinator_forbidden(client):
    """GET /available returns 403 for PLACEMENT_COORDINATOR."""
    token = register_coordinator(client, "coord_avail@example.com")
    res = client.get("/api/v1/assessments/available", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_assessment_available_prerequisites_check(client, db_session):
    """Test /available endpoint displays accurate availability flags."""
    token, profile_id = register_student(client, "avail_student@example.com")

    # Newly registered: student skills are initialized or empty
    res = client.get("/api/v1/assessments/available", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # If student has skills registered, verify practical is not available without certificate
    for item in data:
        assert item["practical_available"] is False
        assert item["followup_available"] is False
        assert "evidence" in item["reason"].lower()


def test_assessment_start_requires_supporting_evidence(client, db_session):
    """POST /start practical assessment without supporting certificate returns 400."""
    token, profile_id = register_student(client, "start_no_ev@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()

    res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 400
    assert "Supporting certificate or project document evidence is required" in res.json()["detail"]


def test_assessment_start_practical_success_and_masking(client, db_session):
    """POST /start succeeds with supporting evidence and returns masked questions."""
    token, profile_id = register_student(client, "start_ok@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()

    # Seed certificate evidence
    add_supporting_evidence(db_session, profile_id, "Python")

    res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 201
    data = res.json()
    assert data["skill_name"] == "Python"
    assert data["type"] == "PRACTICAL"
    assert data["status"] == "PENDING"
    assert len(data["questions"]) >= 3

    # Security check: verify no correct_answer or explanation in payload
    for q in data["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q

    # GET /{id} while pending also masks answers
    get_res = client.get(f"/api/v1/assessments/{data['id']}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["status"] == "PENDING"
    for q in get_data["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q


def test_assessment_start_idempotent_for_pending(client, db_session):
    """POST /start returns active pending assessment without creating duplicate."""
    token, profile_id = register_student(client, "idempotent_start@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, profile_id, "Python")

    res1 = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 201
    id1 = res1.json()["id"]

    res2 = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 201
    id2 = res2.json()["id"]

    assert id1 == id2


def test_assessment_submit_scoring_pass(client, db_session):
    """Submitting >= 70% passes assessment and updates skill to SKILL_ASSESSED."""
    token, profile_id = register_student(client, "submit_pass@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, profile_id, "Python")

    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assessment_id = start_res.json()["id"]

    # Submit 100% correct answers
    raw_questions = get_assessment_questions("Python", "PRACTICAL")
    correct_answers = {q["id"]: q["correct_answer"] for q in raw_questions}

    sub_res = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={
        "answers": correct_answers
    }, headers={"Authorization": f"Bearer {token}"})

    assert sub_res.status_code == 200
    res_data = sub_res.json()
    assert res_data["score"] == 100.0
    assert res_data["passed"] is True
    assert res_data["status"] == "COMPLETED"
    assert res_data["new_skill_status"] == SkillVerificationStatus.SKILL_ASSESSED.value
    assert len(res_data["feedback"]) == len(raw_questions)
    assert all(f["is_correct"] for f in res_data["feedback"])


def test_assessment_submit_scoring_fail(client, db_session):
    """Submitting incorrect answers marks assessment FAILED and preserves EVIDENCE_SUPPORTED."""
    token, profile_id = register_student(client, "submit_fail@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, profile_id, "Python")

    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assessment_id = start_res.json()["id"]

    # Submit completely wrong answers
    raw_questions = get_assessment_questions("Python", "PRACTICAL")
    wrong_answers = {q["id"]: "completely_wrong_answer" for q in raw_questions}

    sub_res = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={
        "answers": wrong_answers
    }, headers={"Authorization": f"Bearer {token}"})

    assert sub_res.status_code == 200
    res_data = sub_res.json()
    assert res_data["score"] == 0.0
    assert res_data["passed"] is False
    assert res_data["status"] == "FAILED"
    # Status should remain EVIDENCE_SUPPORTED
    assert res_data["new_skill_status"] == SkillVerificationStatus.EVIDENCE_SUPPORTED.value


def test_assessment_submit_already_completed_fails(client, db_session):
    """Submitting an assessment that is already COMPLETED returns 400."""
    token, profile_id = register_student(client, "submit_twice@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, profile_id, "Python")

    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assessment_id = start_res.json()["id"]

    # Submit once
    client.post(f"/api/v1/assessments/{assessment_id}/submit", json={"answers": {}}, headers={"Authorization": f"Bearer {token}"})

    # Submit again
    res2 = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={"answers": {}}, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 400
    assert "already been submitted" in res2.json()["detail"]


def test_assessment_ownership_isolation(client, db_session):
    """Student B cannot view or submit Student A's assessment."""
    token_a, prof_a = register_student(client, "student_a@example.com")
    token_b, prof_b = register_student(client, "student_b@example.com")

    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, prof_a, "Python")

    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token_a}"})
    assessment_id = start_res.json()["id"]

    # Student B tries to GET Student A's assessment -> 403
    get_res = client.get(f"/api/v1/assessments/{assessment_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_res.status_code == 403

    # Student B tries to submit Student A's assessment -> 403
    sub_res = client.post(f"/api/v1/assessments/{assessment_id}/submit", json={"answers": {}}, headers={"Authorization": f"Bearer {token_b}"})
    assert sub_res.status_code == 403


def test_assessment_followup_prerequisites(client, db_session):
    """Follow-up assessment requires passed practical assessment AND GitHub repo evidence."""
    token, profile_id = register_student(client, "followup_prereq@example.com")
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()

    # Case 1: Neither practical nor GitHub evidence -> 400
    res1 = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "FOLLOW_UP"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 400
    assert "Practical assessment must be completed" in res1.json()["detail"]

    # Add certificate & pass practical assessment
    add_supporting_evidence(db_session, profile_id, "Python")
    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    raw_q = get_assessment_questions("Python", "PRACTICAL")
    client.post(f"/api/v1/assessments/{start_res.json()['id']}/submit", json={
        "answers": {q["id"]: q["correct_answer"] for q in raw_q}
    }, headers={"Authorization": f"Bearer {token}"})

    # Case 2: Practical passed, but no GitHub project evidence -> 400
    res2 = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "FOLLOW_UP"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 400
    assert "GitHub repository evidence mapped to this skill is required" in res2.json()["detail"]

    # Case 3: Add GitHub evidence -> Success (201)
    add_github_evidence(db_session, profile_id, "Python")
    res3 = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "FOLLOW_UP"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res3.status_code == 201
    assert res3.json()["type"] == "FOLLOW_UP"


def test_assessment_full_forward_lifecycle_matplotlib(client, db_session):
    """
    Complete forward lifecycle test for Matplotlib:
    1. Upload certificate -> EVIDENCE_SUPPORTED
    2. Pass Practical assessment -> SKILL_ASSESSED
    3. Add GitHub repo evidence -> Still SKILL_ASSESSED
    4. Pass Follow-up assessment -> SKILL_VERIFIED!
    """
    token, profile_id = register_student(client, "lifecycle_mpl@example.com")
    mpl_skill = db_session.query(Skill).filter(Skill.name == "Matplotlib").first()

    # Step 1: Upload certificate evidence
    add_supporting_evidence(db_session, profile_id, "Matplotlib")
    # Refresh student profile
    me = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"}).json()
    mpl_state = next(s for s in me["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_state["verification_status"] == SkillVerificationStatus.EVIDENCE_SUPPORTED.value

    # Step 2: Start and pass Practical Assessment
    p_start = client.post("/api/v1/assessments/start", json={
        "skill_id": mpl_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {token}"})
    assert p_start.status_code == 201

    p_raw = get_assessment_questions("Matplotlib", "PRACTICAL")
    p_submit = client.post(f"/api/v1/assessments/{p_start.json()['id']}/submit", json={
        "answers": {q["id"]: q["correct_answer"] for q in p_raw}
    }, headers={"Authorization": f"Bearer {token}"})
    assert p_submit.status_code == 200
    assert p_submit.json()["new_skill_status"] == SkillVerificationStatus.SKILL_ASSESSED.value

    # Verify student profile shows SKILL_ASSESSED
    me2 = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"}).json()
    mpl_state2 = next(s for s in me2["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_state2["verification_status"] == SkillVerificationStatus.SKILL_ASSESSED.value

    # Step 3: Add GitHub repository evidence
    add_github_evidence(db_session, profile_id, "Matplotlib")

    # Step 4: Start and pass Follow-Up Assessment
    fu_start = client.post("/api/v1/assessments/start", json={
        "skill_id": mpl_skill.id,
        "type": "FOLLOW_UP"
    }, headers={"Authorization": f"Bearer {token}"})
    assert fu_start.status_code == 201

    fu_raw = get_assessment_questions("Matplotlib", "FOLLOW_UP")
    fu_submit = client.post(f"/api/v1/assessments/{fu_start.json()['id']}/submit", json={
        "answers": {q["id"]: q["correct_answer"] for q in fu_raw}
    }, headers={"Authorization": f"Bearer {token}"})
    assert fu_submit.status_code == 200
    assert fu_submit.json()["new_skill_status"] == SkillVerificationStatus.SKILL_VERIFIED.value

    # Step 5: Final student profile confirmation
    me3 = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"}).json()
    mpl_state3 = next(s for s in me3["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_state3["verification_status"] == SkillVerificationStatus.SKILL_VERIFIED.value


def test_assessment_history_student_and_coordinator_audit(client, db_session):
    """Test assessment history retrieval for student and audit view for coordinator."""
    s_token, profile_id = register_student(client, "history_student@example.com")
    c_token = register_coordinator(client, "history_coord@example.com")

    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    add_supporting_evidence(db_session, profile_id, "Python")

    # Take and submit assessment
    start_res = client.post("/api/v1/assessments/start", json={
        "skill_id": py_skill.id,
        "type": "PRACTICAL"
    }, headers={"Authorization": f"Bearer {s_token}"})
    assessment_id = start_res.json()["id"]

    raw_q = get_assessment_questions("Python", "PRACTICAL")
    client.post(f"/api/v1/assessments/{assessment_id}/submit", json={
        "answers": {q["id"]: q["correct_answer"] for q in raw_q}
    }, headers={"Authorization": f"Bearer {s_token}"})

    # 1. Student views own history
    hist_res = client.get("/api/v1/assessments/history", headers={"Authorization": f"Bearer {s_token}"})
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
    assert hist_res.json()[0]["id"] == assessment_id

    # 2. Coordinator views student history via student profile ID
    coord_res = client.get(f"/api/v1/assessments/student/{profile_id}", headers={"Authorization": f"Bearer {c_token}"})
    assert coord_res.status_code == 200
    assert len(coord_res.json()) >= 1
    assert coord_res.json()[0]["id"] == assessment_id

    # 3. Student cannot access coordinator audit endpoint -> 403
    forbidden_res = client.get(f"/api/v1/assessments/student/{profile_id}", headers={"Authorization": f"Bearer {s_token}"})
    assert forbidden_res.status_code == 403
