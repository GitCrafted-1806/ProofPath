from app.models.user import User, UserRole


def test_registration_success(client, db_session):
    """Test successful student user registration."""
    payload = {
        "email": "newstudent@example.com",
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Test Student",
        "qualification": "B.Tech",
        "college_name": "NIT",
        "branch": "CSE",
        "academic_year": 2026,
        "cgpa": 8.0
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@example.com"
    assert data["role"] == "STUDENT"
    assert "id" in data

    # Verify user exists in database and password is encrypted
    user = db_session.query(User).filter(User.email == "newstudent@example.com").first()
    assert user is not None
    assert user.hashed_password != "Password123!"
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")


def test_duplicate_email_rejected(client):
    """Test registering with an existing email returns 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "role": "STUDENT"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_login_success_and_token(client):
    """Test valid credentials return a JWT access token."""
    client.post("/api/v1/auth/register", json={
        "email": "loginuser@example.com",
        "password": "SecurePassword123!",
        "role": "STUDENT"
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "loginuser@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "STUDENT"
    assert data["email"] == "loginuser@example.com"


def test_login_invalid_password(client):
    """Test login failure on incorrect password."""
    client.post("/api/v1/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "CorrectPassword!",
        "role": "STUDENT"
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPassword!"
    })
    assert login_res.status_code == 401
    assert "Invalid email or password" in login_res.json()["detail"]


def test_auth_me_requires_token(client):
    """Test /api/v1/auth/me rejects unauthenticated requests."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_auth_me_with_valid_token(client):
    """Test /api/v1/auth/me returns current user details with valid token."""
    reg = client.post("/api/v1/auth/register", json={
        "email": "me_test@example.com",
        "password": "Password123!",
        "role": "PLACEMENT_COORDINATOR"
    })
    assert reg.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "email": "me_test@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "me_test@example.com"
    assert me_data["role"] == "PLACEMENT_COORDINATOR"
