"""Unit & integration tests for student profile endpoints."""
import pytest
from app.models.student_profile import StudentProfile


def register_student(client, email="stud_prof_test@example.com", name="Initial Name"):
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": name,
        "cgpa": 8.0,
        "branch": "CSE",
        "college_name": "Test Engineering College",
        "academic_year": 2026,
        "qualification": "B.Tech"
    })
    assert res.status_code == 201
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_get_and_patch_student_profile(client):
    token = register_student(client)

    # 1. GET /me
    get_res = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["full_name"] == "Initial Name"
    assert data["cgpa"] == 8.0
    public_id = data["public_profile_id"]
    assert public_id.startswith("prf_")

    # 2. PATCH /me with updated fields
    patch_res = client.patch("/api/v1/students/me", json={
        "full_name": "Updated Name",
        "cgpa": 9.25,
        "branch": "AI/ML",
        "college_name": "Top Tech Institute"
    }, headers={"Authorization": f"Bearer {token}"})
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["full_name"] == "Updated Name"
    assert updated["cgpa"] == 9.25
    assert updated["branch"] == "AI/ML"
    assert updated["college_name"] == "Top Tech Institute"

    # 3. GET /me again to verify persistence
    get_res2 = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    assert get_res2.status_code == 200
    assert get_res2.json()["full_name"] == "Updated Name"
    assert get_res2.json()["cgpa"] == 9.25

    # 4. Public Profile view without auth token
    pub_res = client.get(f"/api/v1/students/public/{public_id}")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["full_name"] == "Updated Name"
    assert pub_data["cgpa"] == 9.25
    # user_id and email should NOT be present in public response
    assert "user_id" not in pub_data
    assert "email" not in pub_data


def test_public_profile_404_if_private(client):
    token = register_student(client, email="private_stud@example.com")
    get_res = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    public_id = get_res.json()["public_profile_id"]

    # Set is_public = False
    client.patch("/api/v1/students/me", json={"is_public": False}, headers={"Authorization": f"Bearer {token}"})

    # Public view should now return 404
    pub_res = client.get(f"/api/v1/students/public/{public_id}")
    assert pub_res.status_code == 404
