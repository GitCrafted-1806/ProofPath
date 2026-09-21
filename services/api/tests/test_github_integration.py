from datetime import datetime, timedelta, timezone
import jwt
import pytest

from app.core.config import settings
from app.models.student_skill import SkillVerificationStatus
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.assessment import Assessment


def register_student(client, email="github_student@example.com", name="GitHub Student"):
    """Helper to register and login a student, returning the access token."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": name,
        "cgpa": 8.0
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return res.json()["access_token"]


def register_coordinator(client, email="github_coord@example.com"):
    """Helper to register and login a placement coordinator."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "PLACEMENT_COORDINATOR"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return res.json()["access_token"]


def test_github_status_not_connected(client):
    """Test that a newly registered student has is_connected=False."""
    token = register_student(client, "student_status_nc@example.com")
    res = client.get("/api/v1/github/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_connected"] is False
    assert data["github_username"] is None


def test_github_oauth_start_requires_student(client):
    """Test that OAuth start endpoint requires authenticated STUDENT role."""
    # 1. Unauthenticated
    unauth_res = client.get("/api/v1/github/oauth/start")
    assert unauth_res.status_code == 401

    # 2. Coordinator (forbidden)
    coord_token = register_coordinator(client, "coord_oauth@example.com")
    coord_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {coord_token}"})
    assert coord_res.status_code == 403

    # 3. Student (success)
    student_token = register_student(client, "student_oauth_start@example.com")
    res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "authorize_url" in data
    assert "state" in data
    assert data["demo_mode"] is True


def test_github_oauth_start_generates_valid_state_jwt(client):
    """Test that OAuth start generates a signed, non-expired state JWT containing student_id."""
    student_token = register_student(client, "student_state_jwt@example.com")
    res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    state_token = res.json()["state"]

    # Decode and verify JWT
    payload = jwt.decode(state_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "github_oauth_state"
    assert "sub" in payload
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_github_callback_without_bearer_token_succeeds(client):
    """
    Test that the OAuth callback does NOT require a Bearer token header.
    GitHub browser redirects do not send authorization headers; security is enforced
    via the signed state JWT.
    """
    student_token = register_student(client, "student_callback_nobearer@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]

    # Invoke callback with NO Authorization header
    callback_res = client.get(f"/api/v1/github/callback?code=demo_oauth_code_123&state={state}")
    assert callback_res.status_code == 200
    data = callback_res.json()
    assert data["is_connected"] is True
    assert data["github_username"] == "octocat-dev"
    assert "access_token" not in data
    assert "encrypted_access_token" not in data


def test_github_callback_invalid_state_rejected(client):
    """Test that tampered or invalid state tokens in callback are rejected with HTTP 400."""
    res = client.get("/api/v1/github/callback?code=demo_code&state=invalid_tampered_state_value")
    assert res.status_code == 400
    assert "Invalid or tampered" in res.json()["detail"]


def test_github_callback_expired_state_rejected(client):
    """Test that expired state tokens are rejected with HTTP 400."""
    expired_payload = {
        "sub": "dummy_student_id",
        "type": "github_oauth_state",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5)
    }
    expired_state = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    res = client.get(f"/api/v1/github/callback?code=demo_code&state={expired_state}")
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


def test_github_status_connected_after_callback(client):
    """Test that after callback, status reflects connected state without leaking tokens."""
    student_token = register_student(client, "student_status_conn@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]

    client.get(f"/api/v1/github/callback?code=demo_oauth_code_123&state={state}")

    status_res = client.get("/api/v1/github/status", headers={"Authorization": f"Bearer {student_token}"})
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["is_connected"] is True
    assert data["github_username"] == "octocat-dev"
    assert data["profile_url"] == "https://github.com/octocat-dev"
    assert "access_token" not in data
    assert "encrypted_access_token" not in data


def test_demo_mode_repository_listing(client):
    """Test that connected student can list mock repositories in DEMO_MODE."""
    student_token = register_student(client, "student_repos@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]
    client.get(f"/api/v1/github/callback?code=demo_oauth_code_123&state={state}")

    repo_res = client.get("/api/v1/github/repositories", headers={"Authorization": f"Bearer {student_token}"})
    assert repo_res.status_code == 200
    repos = repo_res.json()
    assert len(repos) >= 3
    repo_names = [r["name"] for r in repos]
    assert "analytics-pipeline" in repo_names
    assert "student-portfolio" in repo_names
    assert "web-scraper" in repo_names

    # Ensure no tokens leaked in repository objects
    for r in repos:
        assert "token" not in str(r).lower()


def test_demo_mode_select_repository_creates_evidence(client):
    """Test selecting a mock repository creates GITHUB_REPO Evidence with SUBMITTED status and mapped skills."""
    student_token = register_student(client, "student_select_repo@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]
    client.get(f"/api/v1/github/callback?code=demo_oauth_code_123&state={state}")

    select_res = client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"repo_full_name": "octocat-dev/analytics-pipeline"}
    )
    assert select_res.status_code == 201
    evidence = select_res.json()

    assert evidence["type"] == "GITHUB_REPO"
    assert evidence["authenticity_state"] == "SUBMITTED"
    assert evidence["file_path"] == "https://github.com/octocat-dev/analytics-pipeline"
    assert "Python" in evidence["mapped_skills"]
    assert "Pandas" in evidence["mapped_skills"]
    assert "Matplotlib" in evidence["mapped_skills"]
    assert "Git/GitHub" in evidence["mapped_skills"]

    # Verify extracted metadata
    meta = evidence["extracted_metadata"]
    assert meta["repo_name"] == "analytics-pipeline"
    assert meta["stars"] == 14
    assert meta["language"] == "Python"
    assert "token" not in str(meta).lower()


def test_github_evidence_listing(client):
    """Test retrieving GitHub project evidence records via GET /github/evidence."""
    student_token = register_student(client, "student_list_ev@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]
    client.get(f"/api/v1/github/callback?code=demo_oauth_code_123&state={state}")

    client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"repo_full_name": "octocat-dev/student-portfolio"}
    )

    ev_res = client.get("/api/v1/github/evidence", headers={"Authorization": f"Bearer {student_token}"})
    assert ev_res.status_code == 200
    evidences = ev_res.json()
    assert len(evidences) >= 1
    assert evidences[0]["type"] == "GITHUB_REPO"
    assert evidences[0]["original_filename"] == "student-portfolio"


def test_unconnected_student_cannot_list_or_select_repos(client):
    """Test that a student who has not connected GitHub cannot list or select repositories."""
    token = register_student(client, "student_unconn@example.com")

    list_res = client.get("/api/v1/github/repositories", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 400
    assert "not connected" in list_res.json()["detail"]

    select_res = client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {token}"},
        json={"repo_full_name": "octocat-dev/analytics-pipeline"}
    )
    assert select_res.status_code == 400
    assert "not connected" in select_res.json()["detail"]


def test_student_ownership_isolation(client):
    """Test that Student B cannot view or access Student A's GitHub project evidence."""
    token_a = register_student(client, "student_a_gh@example.com", "Student A")
    token_b = register_student(client, "student_b_gh@example.com", "Student B")

    # Student A connects and selects repo
    start_a = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {token_a}"})
    client.get(f"/api/v1/github/callback?code=demo_code&state={start_a.json()['state']}")
    client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"repo_full_name": "octocat-dev/analytics-pipeline"}
    )

    # Student B has not connected, should see 0 evidence
    ev_b = client.get("/api/v1/github/evidence", headers={"Authorization": f"Bearer {token_b}"})
    assert ev_b.status_code == 200
    assert len(ev_b.json()) == 0


def test_coordinator_can_view_student_github_evidence(client, db_session):
    """Test that a Placement Coordinator can inspect student's GitHub evidence."""
    student_token = register_student(client, "student_coord_gh@example.com", "Student For Coord")
    coord_token = register_coordinator(client, "coord_inspect_gh@example.com")

    # Connect student & select repo
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    client.get(f"/api/v1/github/callback?code=demo_code&state={start_res.json()['state']}")
    select_res = client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"repo_full_name": "octocat-dev/web-scraper"}
    )
    student_id = select_res.json()["student_id"]

    # Coordinator inspects evidence filtering by student_id
    coord_ev = client.get(
        f"/api/v1/github/evidence?student_id={student_id}",
        headers={"Authorization": f"Bearer {coord_token}"}
    )
    assert coord_ev.status_code == 200
    evidences = coord_ev.json()
    assert len(evidences) == 1
    assert evidences[0]["type"] == "GITHUB_REPO"


def test_github_evidence_integrates_with_deterministic_verification_engine(client, db_session):
    """
    Test deterministic verification engine integration:
    - GitHub evidence alone does NOT verify a skill without supporting evidence (Rule 1).
    - Certificate + Practical Assessment + GitHub Project Evidence + Follow-up Assessment produces SKILL_VERIFIED (Rule 4).
    """
    token = register_student(client, "student_engine_rules@example.com", "Engine Tester")

    # 1. Connect GitHub and select repo
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {token}"})
    client.get(f"/api/v1/github/callback?code=demo_code&state={start_res.json()['state']}")
    select_res = client.post(
        "/api/v1/github/repositories/select",
        headers={"Authorization": f"Bearer {token}"},
        json={"repo_full_name": "octocat-dev/analytics-pipeline"}
    )
    assert select_res.status_code == 201
    student_id = select_res.json()["student_id"]

    # Check skill status: Python has project evidence, but NO supporting evidence (certificate)
    me_res = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_map = {s["skill_name"]: s["verification_status"] for s in me_res.json()["skills"]}
    # Rule 1: Without supporting evidence (certificate), remains UNVERIFIED
    assert skills_map["Python"] == SkillVerificationStatus.UNVERIFIED.value

    # 2. Add supporting certificate evidence for Python
    cert_ev = Evidence(
        student_id=student_id,
        type=EvidenceType.CERTIFICATE,
        file_path="/uploads/cert.pdf",
        authenticity_state=AuthenticityState.SUBMITTED,
        mapped_skills=["Python"]
    )
    db_session.add(cert_ev)
    db_session.commit()

    # Query skill_id for Python
    python_skill_id = [s["skill_id"] for s in me_res.json()["skills"] if s["skill_name"] == "Python"][0]

    # Add Practical Assessment (passed)
    prac = Assessment(
        student_id=student_id,
        skill_id=python_skill_id,
        type="PRACTICAL",
        status="COMPLETED",
        score=90.0,
        passed=True,
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(prac)
    db_session.commit()

    # Now has Certificate + Assessment + GitHub Repo, but no Follow-up -> SKILL_ASSESSED
    from app.services.verification_engine import update_and_persist_skill_status
    update_and_persist_skill_status(student_id, python_skill_id, db_session)

    me_res2 = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_map2 = {s["skill_name"]: s["verification_status"] for s in me_res2.json()["skills"]}
    assert skills_map2["Python"] == SkillVerificationStatus.SKILL_ASSESSED.value

    # 3. Add Follow-up Assessment (passed) -> Reaches SKILL_VERIFIED!
    followup = Assessment(
        student_id=student_id,
        skill_id=python_skill_id,
        type="FOLLOW_UP",
        status="COMPLETED",
        score=95.0,
        passed=True,
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(followup)
    db_session.commit()

    update_and_persist_skill_status(student_id, python_skill_id, db_session)

    me_res3 = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_map3 = {s["skill_name"]: s["verification_status"] for s in me_res3.json()["skills"]}
    assert skills_map3["Python"] == SkillVerificationStatus.SKILL_VERIFIED.value


def test_github_disconnect(client):
    """Test disconnecting a GitHub account removes connection."""
    student_token = register_student(client, "student_disc@example.com")
    start_res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
    state = start_res.json()["state"]
    client.get(f"/api/v1/github/callback?code=demo_code&state={state}")

    # Confirm connected
    status_before = client.get("/api/v1/github/status", headers={"Authorization": f"Bearer {student_token}"})
    assert status_before.json()["is_connected"] is True

    # Disconnect
    disc_res = client.post("/api/v1/github/disconnect", headers={"Authorization": f"Bearer {student_token}"})
    assert disc_res.status_code == 200

    # Confirm disconnected
    status_after = client.get("/api/v1/github/status", headers={"Authorization": f"Bearer {student_token}"})
    assert status_after.json()["is_connected"] is False


def test_live_mode_missing_credentials_raises_error(client):
    """Test that when DEMO_MODE=false and credentials are not configured, OAuth start raises an error."""
    student_token = register_student(client, "student_live_unconf@example.com")

    # Temporarily simulate DEMO_MODE=False without configured secrets
    original_demo_mode = settings.DEMO_MODE
    original_client_id = settings.GITHUB_CLIENT_ID
    original_client_secret = settings.GITHUB_CLIENT_SECRET
    try:
        settings.DEMO_MODE = False
        settings.GITHUB_CLIENT_ID = None
        settings.GITHUB_CLIENT_SECRET = None

        res = client.get("/api/v1/github/oauth/start", headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 500
        assert "not configured" in res.json()["detail"].lower()
    finally:
        settings.DEMO_MODE = original_demo_mode
        settings.GITHUB_CLIENT_ID = original_client_id
        settings.GITHUB_CLIENT_SECRET = original_client_secret
