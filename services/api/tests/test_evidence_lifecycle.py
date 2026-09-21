import fitz
from pathlib import Path
import pytest
from app.models.student_skill import SkillVerificationStatus


def create_pdf(text: str) -> bytes:
    """Helper to create a PDF with text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    content = doc.tobytes()
    doc.close()
    return content


def register_and_login(client, email: str, role: str = "STUDENT", full_name: str = "Student"):
    """Helper to register and login a user."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": role,
        "full_name": full_name,
        "cgpa": 8.0
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return res.json()["access_token"]


def test_uploaded_certificate_has_submitted_state(client):
    """Verify certificate uploaded with recognized issuer remains SUBMITTED by default."""
    token = register_and_login(client, "student_sub@example.com", "STUDENT", "Submitted Tester")
    pdf_bytes = create_pdf("Coursera Verified Certificate in Python Programming. Awarded to Submitted Tester.")

    res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("coursera_cert.pdf", pdf_bytes, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    assert res.status_code == 201
    data = res.json()
    # Corrected requirement: MUST be SUBMITTED, not automatically SOURCE_SUPPORTED
    assert data["authenticity_state"] == "SUBMITTED"
    assert data["extracted_metadata"]["issuer"] == "Coursera"


def test_student_list_me_evidence(client):
    """Verify student can retrieve all their uploaded evidence records."""
    token = register_and_login(client, "student_list@example.com", "STUDENT", "List Tester")
    pdf1 = create_pdf("Python course certificate")
    pdf2 = create_pdf("Pandas data analysis document")

    # Upload 2 files
    client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("cert1.pdf", pdf1, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("doc2.pdf", pdf2, "application/pdf")},
        data={"type": "PROJECT_DOCUMENT"}
    )

    list_res = client.get(
        "/api/v1/evidence/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_res.status_code == 200
    evidence_list = list_res.json()
    assert len(evidence_list) == 2


def test_student_ownership_isolation(client):
    """Verify Student B cannot view or download Student A's evidence."""
    token_a = register_and_login(client, "student_a@example.com", "STUDENT", "Student A")
    token_b = register_and_login(client, "student_b@example.com", "STUDENT", "Student B")

    pdf = create_pdf("Student A confidential certificate in Python")
    upload_res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("student_a_cert.pdf", pdf, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    evidence_id = upload_res.json()["id"]

    # Student B tries to get details
    detail_res = client.get(
        f"/api/v1/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert detail_res.status_code == 403

    # Student B tries to download
    download_res = client.get(
        f"/api/v1/evidence/{evidence_id}/download",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert download_res.status_code == 403


def test_coordinator_can_view_and_verify_evidence(client):
    """Verify Coordinator can view student evidence and transition state to INSTITUTION_VERIFIED."""
    student_token = register_and_login(client, "student_c@example.com", "STUDENT", "Student C")
    coord_token = register_and_login(client, "coord_c@example.com", "PLACEMENT_COORDINATOR")

    pdf = create_pdf("Matplotlib Data Visualization Certificate")
    upload_res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("matplotlib_cert.pdf", pdf, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    evidence_id = upload_res.json()["id"]

    # Coordinator views evidence details
    coord_view = client.get(
        f"/api/v1/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {coord_token}"}
    )
    assert coord_view.status_code == 200
    assert coord_view.json()["id"] == evidence_id

    # Coordinator downloads file
    coord_download = client.get(
        f"/api/v1/evidence/{evidence_id}/download",
        headers={"Authorization": f"Bearer {coord_token}"}
    )
    assert coord_download.status_code == 200

    # Coordinator verifies evidence
    verify_res = client.patch(
        f"/api/v1/evidence/{evidence_id}/verify",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={
            "authenticity_state": "INSTITUTION_VERIFIED",
            "remarks": "Verified physical certificate with university registrar."
        }
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["authenticity_state"] == "INSTITUTION_VERIFIED"


def test_evidence_upload_triggers_verification_engine(client):
    """Verify evidence upload triggers verification engine to update skill to EVIDENCE_SUPPORTED."""
    token = register_and_login(client, "student_engine@example.com", "STUDENT", "Engine Tester")

    # Before upload: all skills should be UNVERIFIED
    me_res = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    skills_before = {s["skill_name"]: s["verification_status"] for s in me_res.json()["skills"]}
    assert skills_before["Python"] == SkillVerificationStatus.UNVERIFIED.value

    # Upload certificate for Python
    pdf = create_pdf("Comprehensive Certificate in Python and Pandas Programming")
    upload_res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("python_cert.pdf", pdf, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    assert upload_res.status_code == 201

    # After upload: Python and Pandas should now be EVIDENCE_SUPPORTED
    me_after = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_after = {s["skill_name"]: s["verification_status"] for s in me_after.json()["skills"]}
    assert skills_after["Python"] == SkillVerificationStatus.EVIDENCE_SUPPORTED.value
    assert skills_after["Pandas"] == SkillVerificationStatus.EVIDENCE_SUPPORTED.value
    assert skills_after["Matplotlib"] == SkillVerificationStatus.UNVERIFIED.value


def test_student_delete_own_evidence_recomputes_status(client):
    """Verify deleting evidence cleans up the file and rolls skill back to UNVERIFIED."""
    token = register_and_login(client, "student_del@example.com", "STUDENT", "Delete Tester")
    pdf = create_pdf("Matplotlib Specialized Certificate")

    upload_res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("mat_cert.pdf", pdf, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    evidence_id = upload_res.json()["id"]

    # Verify skill is now EVIDENCE_SUPPORTED
    me_res = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_map = {s["skill_name"]: s["verification_status"] for s in me_res.json()["skills"]}
    assert skills_map["Matplotlib"] == SkillVerificationStatus.EVIDENCE_SUPPORTED.value

    # Delete evidence
    del_res = client.delete(
        f"/api/v1/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert del_res.status_code == 200

    # Verify skill transitioned back to UNVERIFIED
    me_res_after = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    skills_map_after = {s["skill_name"]: s["verification_status"] for s in me_res_after.json()["skills"]}
    assert skills_map_after["Matplotlib"] == SkillVerificationStatus.UNVERIFIED.value


def test_cannot_delete_institution_verified_evidence(client):
    """Verify student cannot delete evidence that has been marked INSTITUTION_VERIFIED."""
    student_token = register_and_login(client, "student_locked@example.com", "STUDENT", "Locked Student")
    coord_token = register_and_login(client, "coord_lock@example.com", "PLACEMENT_COORDINATOR")

    pdf = create_pdf("Git and GitHub Master Certificate")
    upload_res = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("git_cert.pdf", pdf, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )
    evidence_id = upload_res.json()["id"]

    # Coordinator marks as verified
    client.patch(
        f"/api/v1/evidence/{evidence_id}/verify",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={"authenticity_state": "INSTITUTION_VERIFIED"}
    )

    # Student attempts deletion
    del_res = client.delete(
        f"/api/v1/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert del_res.status_code == 400
    assert "Cannot delete evidence that has been verified" in del_res.json()["detail"]
