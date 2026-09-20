def test_student_can_access_student_me(client):
    """Verify students can access the student profile endpoint."""
    client.post("/api/v1/auth/register", json={
        "email": "student1@example.com",
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Student One",
        "cgpa": 8.5
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student1@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = response_data = res.json()
    assert response_data["full_name"] == "Student One"
    assert response_data["cgpa"] == 8.5
    assert len(response_data["skills"]) == 4


def test_coordinator_denied_from_student_me(client):
    """Verify placement coordinators cannot call student-only endpoints."""
    client.post("/api/v1/auth/register", json={
        "email": "coord@example.com",
        "password": "Password123!",
        "role": "PLACEMENT_COORDINATOR"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "coord@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]
