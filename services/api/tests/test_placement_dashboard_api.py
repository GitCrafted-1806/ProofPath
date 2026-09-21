import pytest
from app.models.user import UserRole
from app.models.student_skill import SkillVerificationStatus
from app.services.demo_seed import seed_demo_data


@pytest.fixture
def seeded_db(db_session):
    """Ensure database has demo seeds available."""
    seed_demo_data(db_session, force_reset=True)
    return db_session


@pytest.fixture
def coordinator_auth(client, seeded_db):
    """Login as placement coordinator and return auth headers."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "coordinator@college.edu", "password": "Password123!"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_auth(client, seeded_db):
    """Login as John Doe (student) and return auth headers."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "john.doe@nit.edu", "password": "Password123!"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_coordinator_rbac_protection(client, seeded_db, student_auth, coordinator_auth):
    """Students must be strictly forbidden from coordinator endpoints."""
    # 1. Student accessing student directory -> 403
    resp = client.get("/api/v1/students", headers=student_auth)
    assert resp.status_code == 403

    # 2. Student creating placement requirement -> 403
    resp = client.post(
        "/api/v1/placements/requirements",
        json={
            "company_name": "Acme Corp",
            "role_title": "Data Analyst",
            "min_cgpa": 7.5,
            "eligible_branches": ["CSE"],
            "required_skills": {"Python": "SKILL_VERIFIED"}
        },
        headers=student_auth
    )
    assert resp.status_code == 403

    # 3. Student requesting assessment for another student -> 403
    resp = client.post(
        "/api/v1/assessments/request",
        json={
            "student_id": "dummy-id",
            "skill_id": "dummy-skill",
            "type": "PRACTICAL"
        },
        headers=student_auth
    )
    assert resp.status_code == 403

    # 4. Coordinator can access student directory -> 200
    resp = client.get("/api/v1/students", headers=coordinator_auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "students" in data
    assert data["total"] >= 2


def test_student_directory_filtering(client, seeded_db, coordinator_auth):
    """Placement coordinator can search and filter directory."""
    # Search by name
    resp = client.get("/api/v1/students?search=John", headers=coordinator_auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("John Doe" in s["full_name"] for s in data["students"])

    # Filter by branch (John Doe is CSE)
    resp = client.get("/api/v1/students?branch=CSE", headers=coordinator_auth)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Filter by non-matching branch
    resp = client.get("/api/v1/students?branch=CivilEngineering", headers=coordinator_auth)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Filter by min CGPA
    resp = client.get("/api/v1/students?min_cgpa=8.0", headers=coordinator_auth)
    assert resp.status_code == 200
    for s in resp.json()["students"]:
        assert s["cgpa"] >= 8.0


def test_coordinator_student_detail_and_evidence(client, seeded_db, coordinator_auth):
    """Coordinator can view any student's profile and evidence documents."""
    # Find John Doe's ID from directory
    dir_resp = client.get("/api/v1/students?search=John", headers=coordinator_auth)
    student = dir_resp.json()["students"][0]
    student_id = student["id"]

    # 1. Get profile
    prof_resp = client.get(f"/api/v1/students/{student_id}", headers=coordinator_auth)
    assert prof_resp.status_code == 200
    prof = prof_resp.json()
    assert prof["full_name"] == "John Doe"
    assert len(prof["skills"]) > 0

    # 2. Get evidence list
    ev_resp = client.get(f"/api/v1/evidence/student/{student_id}", headers=coordinator_auth)
    assert ev_resp.status_code == 200
    evidences = ev_resp.json()
    assert isinstance(evidences, list)
    assert len(evidences) >= 1

    # 3. Get assessment history
    as_resp = client.get(f"/api/v1/assessments/student/{student_id}", headers=coordinator_auth)
    assert as_resp.status_code == 200
    assessments = as_resp.json()
    assert isinstance(assessments, list)


def test_placement_requirements_crud(client, seeded_db, coordinator_auth):
    """Test full CRUD operations on placement requirements."""
    # Create requirement
    create_payload = {
        "company_name": "Google",
        "role_title": "Data Systems Engineer",
        "min_cgpa": 8.0,
        "eligible_branches": ["CSE", "IT"],
        "required_skills": {
            "Python": "SKILL_VERIFIED",
            "Pandas": "SKILL_ASSESSED"
        }
    }
    create_resp = client.post(
        "/api/v1/placements/requirements",
        json=create_payload,
        headers=coordinator_auth
    )
    assert create_resp.status_code == 201
    req_data = create_resp.json()
    req_id = req_data["id"]
    assert req_data["company_name"] == "Google"
    assert req_data["min_cgpa"] == 8.0

    # List requirements
    list_resp = client.get("/api/v1/placements/requirements", headers=coordinator_auth)
    assert list_resp.status_code == 200
    all_reqs = list_resp.json()
    assert any(r["id"] == req_id for r in all_reqs)

    # Get requirement detail
    detail_resp = client.get(f"/api/v1/placements/requirements/{req_id}", headers=coordinator_auth)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["role_title"] == "Data Systems Engineer"

    # Delete requirement
    del_resp = client.delete(f"/api/v1/placements/requirements/{req_id}", headers=coordinator_auth)
    assert del_resp.status_code == 204

    # Verify deleted
    get_del = client.get(f"/api/v1/placements/requirements/{req_id}", headers=coordinator_auth)
    assert get_del.status_code == 404


def test_deterministic_matching_logic(client, seeded_db, coordinator_auth):
    """
    Test deterministic candidate matching against actual DB data.
    Ensures:
    - Calculated dynamically from DB
    - No scores, no candidate ranking, no winner labels
    - Factual criteria compliance and failure reasons
    """
    # 1. Create a requirement that John Doe SHOULD match:
    # John Doe has CGPA 8.2, Branch 'CSE', Python SKILL_VERIFIED, Pandas SKILL_ASSESSED
    easy_req = client.post(
        "/api/v1/placements/requirements",
        json={
            "company_name": "Alpha Tech",
            "role_title": "Junior Python Developer",
            "min_cgpa": 7.0,
            "eligible_branches": ["CSE"],
            "required_skills": {
                "Python": "SKILL_VERIFIED"
            }
        },
        headers=coordinator_auth
    ).json()

    match_resp = client.post(
        f"/api/v1/placements/requirements/{easy_req['id']}/match",
        headers=coordinator_auth
    )
    assert match_resp.status_code == 200
    data = match_resp.json()
    assert data["total_candidates"] >= 2

    # Locate John Doe in matches
    john_matches = [m for m in data["matches"] if "John Doe" in m["full_name"]]
    assert len(john_matches) == 1
    john = john_matches[0]
    assert john["is_matched"] is True
    assert john["criteria_results"]["cgpa"]["passed"] is True
    assert john["criteria_results"]["branch"]["passed"] is True
    assert john["criteria_results"]["skills"]["Python"]["passed"] is True
    assert len(john["failure_reasons"]) == 0

    # 2. Create a requirement that John Doe MUST NOT match (e.g. CGPA 9.5):
    hard_req = client.post(
        "/api/v1/placements/requirements",
        json={
            "company_name": "HighBar Labs",
            "role_title": "Principal Architect",
            "min_cgpa": 9.5,
            "eligible_branches": ["CSE"],
            "required_skills": {
                "Python": "SKILL_VERIFIED"
            }
        },
        headers=coordinator_auth
    ).json()

    match_resp_hard = client.post(
        f"/api/v1/placements/requirements/{hard_req['id']}/match",
        headers=coordinator_auth
    )
    assert match_resp_hard.status_code == 200
    hard_data = match_resp_hard.json()
    john_hard = [m for m in hard_data["matches"] if "John Doe" in m["full_name"]][0]
    assert john_hard["is_matched"] is False
    assert john_hard["criteria_results"]["cgpa"]["passed"] is False
    assert any("below the minimum required" in reason for reason in john_hard["failure_reasons"])

    # Check there are no winner labels, ranking indices, or score fields in CandidateMatchItem
    for m in hard_data["matches"]:
        assert "rank" not in m
        assert "score" not in m
        assert "winner" not in m
        assert "best_candidate" not in m


def test_coordinator_assessment_request(client, seeded_db, coordinator_auth):
    """Coordinator can explicitly request an assessment for a student."""
    dir_resp = client.get("/api/v1/students?search=Jane", headers=coordinator_auth)
    assert dir_resp.status_code == 200
    students = dir_resp.json()["students"]
    assert len(students) > 0
    jane = students[0]

    # Find Python skill ID
    python_skill = next((s for s in jane["skills"] if s["skill_name"] == "Python"), None)
    skill_id = python_skill["skill_id"] if python_skill else "Python"

    req_resp = client.post(
        "/api/v1/assessments/request",
        json={
            "student_id": jane["id"],
            "skill_id": skill_id,
            "type": "PRACTICAL"
        },
        headers=coordinator_auth
    )
    assert req_resp.status_code == 201
    res_data = req_resp.json()
    assert res_data["status"] in ("SUCCESS", "ALREADY_PENDING", "ALREADY_PASSED")
    assert res_data["student_id"] == jane["id"]


def test_secure_csv_export(client, seeded_db, coordinator_auth):
    """
    CSV export must contain strictly safe candidate data and criteria results.
    Never export passwords, hashes, tokens, or private paths.
    """
    req = client.post(
        "/api/v1/placements/requirements",
        json={
            "company_name": "SecureCorp",
            "role_title": "Security Analyst",
            "min_cgpa": 6.5,
            "eligible_branches": ["CSE"],
            "required_skills": {"Python": "EVIDENCE_SUPPORTED"}
        },
        headers=coordinator_auth
    ).json()

    export_resp = client.get(
        f"/api/v1/placements/requirements/{req['id']}/export",
        headers=coordinator_auth
    )
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["Content-Type"]
    assert "attachment" in export_resp.headers["Content-Disposition"]

    csv_text = export_resp.text
    # Verify header
    assert "Student Name,Email,College,Branch,Academic Year,CGPA,Match Status" in csv_text
    # Verify candidate present
    assert "John Doe" in csv_text

    # SECURITY ASSERTIONS: Strictly NO sensitive tokens or storage internals
    forbidden_tokens = [
        "password",
        "hashed_password",
        "access_token",
        "bearer",
        "jwt",
        "github_pat",
        "secret",
        "private_key",
        "/storage/uploads",
    ]
    csv_lower = csv_text.lower()
    for token in forbidden_tokens:
        assert token not in csv_lower, f"Forbidden sensitive token '{token}' found in CSV export!"


def test_evidence_verification_authorization_preservation(client, seeded_db, student_auth, coordinator_auth):
    """
    PRESERVE EVIDENCE AUTHORIZATION:
    Existing RBAC rules must be respected:
    Only coordinator role can invoke PATCH /api/v1/evidence/{id}/verify.
    Students must receive 403 Forbidden.
    """
    # Get John's evidence
    ev_resp = client.get("/api/v1/evidence/me", headers=student_auth)
    assert ev_resp.status_code == 200
    evidences = ev_resp.json()
    assert len(evidences) > 0
    target_evidence_id = evidences[0]["id"]

    # Student tries to verify own evidence -> 403 Forbidden
    student_attempt = client.patch(
        f"/api/v1/evidence/{target_evidence_id}/verify",
        json={"authenticity_state": "INSTITUTION_VERIFIED", "remarks": "Student self-verifying"},
        headers=student_auth
    )
    assert student_attempt.status_code == 403

    # Coordinator verifies evidence -> 200 OK
    coord_attempt = client.patch(
        f"/api/v1/evidence/{target_evidence_id}/verify",
        json={"authenticity_state": "INSTITUTION_VERIFIED", "remarks": "Verified by College Placement Office"},
        headers=coordinator_auth
    )
    assert coord_attempt.status_code == 200
    assert coord_attempt.json()["authenticity_state"] == "INSTITUTION_VERIFIED"
