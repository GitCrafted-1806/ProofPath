"""
Comprehensive validation test suite verifying production-grade input validation across ProofPath.
Tests constraints on types, formats, lengths, ranges, and character sets on both registration and mutation endpoints.
"""

import uuid
import pytest
from app.services.demo_seed import seed_demo_data


@pytest.fixture
def clean_db(db_session):
    seed_demo_data(db_session, force_reset=True)
    return db_session


@pytest.fixture
def coordinator_token(client, clean_db):
    resp = client.post("/api/v1/auth/login", json={
        "email": "coordinator@college.edu",
        "password": "Password123!"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def student_token(client, clean_db):
    resp = client.post("/api/v1/auth/login", json={
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


# =========================================================================
# 1. STUDENT REGISTRATION VALIDATION
# =========================================================================

def test_registration_valid_full_name(client, clean_db):
    """Test valid names with letters, spaces, hyphens, and apostrophes."""
    valid_names = [
        "John Doe",
        "Mary-Anne Smith",
        "O'Connor",
        "Dr. Alex Chen",
        "Jean-Luc Picard Jr."
    ]
    for i, name in enumerate(valid_names):
        resp = client.post("/api/v1/auth/register", json={
            "email": f"valid_name_{i}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": name,
            "college_name": "National Institute of Technology",
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": 8.5,
            "skills": ["Python"]
        })
        assert resp.status_code == 201, f"Failed for valid name '{name}': {resp.json()}"


def test_registration_invalid_names(client, clean_db):
    """Test rejection of single characters, digits, arbitrary symbols, and pure punctuation."""
    invalid_names = [
        "A",              # Too short / single letter
        "John123",        # Contains digits
        "John@Doe",       # Special char @
        "12345",          # Only digits
        "-.-'",           # No meaningful letters
        "   ",            # Whitespace only
        "A" * 81,         # Exceeds 80 characters
        "<script>alert()</script>",  # XSS attempt
    ]
    for name in invalid_names:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"invalid_{abs(hash(name))}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": name,
            "college_name": "NIT",
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 422, f"Expected 422 for invalid name '{name}', got {resp.status_code}"


def test_registration_institution_validation(client, clean_db):
    """Test valid and invalid college/institution names."""
    # Valid institutions
    valid_colleges = [
        "IIT-Madras",
        "University of Technology & Science",
        "College of Engineering (Autonomous)",
        "St. John's Institute/Academy"
    ]
    for i, col in enumerate(valid_colleges):
        resp = client.post("/api/v1/auth/register", json={
            "email": f"col_{i}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": col,
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 201, f"Failed for valid college '{col}': {resp.json()}"

    # Invalid institutions
    invalid_colleges = [
        "A",             # Too short
        "   ",           # Whitespace only
        "X" * 121,       # Too long (> 120)
        "$$$###@@@",     # No alphanumeric
    ]
    for col in invalid_colleges:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"badcol_{abs(hash(col))}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": col,
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 422, f"Expected 422 for invalid college '{col}', got {resp.status_code}"


def test_registration_branch_validation(client, clean_db):
    """Test valid and invalid branch/major names."""
    valid_branches = [
        "Computer Science & Engineering",
        "ECE",
        "EE / Electronics",
        "Bio-Tech."
    ]
    for i, b in enumerate(valid_branches):
        resp = client.post("/api/v1/auth/register", json={
            "email": f"branch_{i}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": b,
            "academic_year": 2026,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 201, f"Failed for valid branch '{b}': {resp.json()}"

    invalid_branches = [
        "A",             # Too short
        "   ",           # Whitespace only
        "B" * 81,        # Too long (> 80)
        "***???",        # Invalid chars
    ]
    for b in invalid_branches:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"badb_{abs(hash(b))}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": b,
            "academic_year": 2026,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 422, f"Expected 422 for invalid branch '{b}', got {resp.status_code}"


def test_registration_graduation_year_validation(client, clean_db):
    """Test graduation year integer range 2000-2040 and format."""
    # Valid years
    for yr in [2000, 2026, 2040]:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"year_{yr}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": "CSE",
            "academic_year": yr,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 201, f"Failed for valid year {yr}: {resp.json()}"

    # Invalid years
    for yr in [1999, 2041, -2026, 202.5, "not_a_year"]:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"badyr_{abs(hash(str(yr)))}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": "CSE",
            "academic_year": yr,
            "cgpa": 8.0,
            "skills": ["Python"]
        })
        assert resp.status_code == 422, f"Expected 422 for invalid year {yr}, got {resp.status_code}"


def test_registration_cgpa_validation(client, clean_db):
    """Test CGPA numeric boundary 0.00-10.00 and max 2 decimal places."""
    # Valid CGPAs
    for val in [0.0, 0.00, 7.5, 8.45, 10.0, 10.00]:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"cgpa_{uuid.uuid4().hex[:8]}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": val,
            "skills": ["Python"]
        })
        assert resp.status_code == 201, f"Failed for valid CGPA {val}: {resp.json()}"

    # Invalid CGPAs
    invalid_cgpas = [
        -0.01,           # Negative
        10.01,           # Above 10
        15.0,            # Way above 10
        8.756,           # 3 decimal places
        9.999,           # 3 decimal places
        "not_a_number",  # Non-numeric
    ]
    for val in invalid_cgpas:
        resp = client.post("/api/v1/auth/register", json={
            "email": f"badcgpa_{uuid.uuid4().hex[:8]}@college.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "full_name": "Valid Student",
            "college_name": "NIT",
            "branch": "CSE",
            "academic_year": 2026,
            "cgpa": val,
            "skills": ["Python"]
        })
        assert resp.status_code == 422, f"Expected 422 for invalid CGPA {val}, got {resp.status_code}"


def test_registration_password_minimum(client, clean_db):
    """Test password must be at least 8 characters."""
    # 7 characters -> rejected
    resp = client.post("/api/v1/auth/register", json={
        "email": "short_pass@college.edu",
        "password": "Short1!",
        "role": "STUDENT"
    })
    assert resp.status_code == 422

    # 8 characters -> accepted
    resp = client.post("/api/v1/auth/register", json={
        "email": "good_pass@college.edu",
        "password": "GoodPass",
        "role": "STUDENT"
    })
    assert resp.status_code == 201


def test_registration_skills_validation(client, clean_db):
    """Test claimed skills must be ProofPath MVP skills and duplicates are deduplicated."""
    # Unknown skill -> 422
    resp = client.post("/api/v1/auth/register", json={
        "email": "unknown_skill@college.edu",
        "password": "Password123!",
        "role": "STUDENT",
        "skills": ["Java", "Python"]
    })
    assert resp.status_code == 422

    # Empty skills list -> 422
    resp = client.post("/api/v1/auth/register", json={
        "email": "empty_skills@college.edu",
        "password": "Password123!",
        "role": "STUDENT",
        "skills": []
    })
    assert resp.status_code == 422

    # Duplicates in skills list -> deduplicated and accepted
    resp = client.post("/api/v1/auth/register", json={
        "email": "dedup_skills@college.edu",
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Dedup Student",
        "college_name": "NIT",
        "branch": "CSE",
        "academic_year": 2026,
        "cgpa": 8.0,
        "skills": ["Python", "Python", "Pandas", "Pandas"]
    })
    assert resp.status_code == 201

    # Login and verify only 2 unique skills created
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "dedup_skills@college.edu",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    prof_resp = client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {token}"})
    assert len(prof_resp.json()["skills"]) == 2


# =========================================================================
# 2. STUDENT PROFILE UPDATE VALIDATION
# =========================================================================

def test_profile_update_validation(client, clean_db, student_token):
    """Verify PATCH /api/v1/students/me enforces same validation rules."""
    headers = {"Authorization": f"Bearer {student_token}"}

    # Invalid name (digits) -> 422
    res = client.patch("/api/v1/students/me", json={"full_name": "JohnDoe99"}, headers=headers)
    assert res.status_code == 422

    # Invalid name (too short) -> 422
    res = client.patch("/api/v1/students/me", json={"full_name": "J"}, headers=headers)
    assert res.status_code == 422

    # Invalid college (empty) -> 422
    res = client.patch("/api/v1/students/me", json={"college_name": "   "}, headers=headers)
    assert res.status_code == 422

    # Invalid branch (symbols) -> 422
    res = client.patch("/api/v1/students/me", json={"branch": "$$$$$"}, headers=headers)
    assert res.status_code == 422

    # Invalid CGPA (> 10) -> 422
    res = client.patch("/api/v1/students/me", json={"cgpa": 10.5}, headers=headers)
    assert res.status_code == 422

    # Invalid CGPA (3 decimals) -> 422
    res = client.patch("/api/v1/students/me", json={"cgpa": 8.125}, headers=headers)
    assert res.status_code == 422

    # Valid update -> 200
    res = client.patch("/api/v1/students/me", json={
        "full_name": "Jonathan Doe",
        "college_name": "National Institute of Technology - Trichy",
        "branch": "Computer Science & Engineering",
        "academic_year": 2026,
        "cgpa": 8.75,
    }, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["full_name"] == "Jonathan Doe"
    assert updated["cgpa"] == 8.75


# =========================================================================
# 3. PLACEMENT REQUIREMENT VALIDATION
# =========================================================================

def test_placement_requirement_validation(client, clean_db, coordinator_token):
    """Verify coordinator placement requirement validation."""
    headers = {"Authorization": f"Bearer {coordinator_token}"}

    # Valid requirement
    res = client.post("/api/v1/placements/requirements", json={
        "company_name": "Google LLC & DeepMind",
        "role_title": "AI Research Engineer (ML/DL)",
        "min_cgpa": 8.5,
        "eligible_branches": ["CSE", "IT"],
        "required_skills": {"Python": "SKILL_VERIFIED"}
    }, headers=headers)
    assert res.status_code == 201

    # Invalid company name (too short) -> 422
    res = client.post("/api/v1/placements/requirements", json={
        "company_name": "X",
        "role_title": "Software Engineer",
        "min_cgpa": 7.0,
    }, headers=headers)
    assert res.status_code == 422

    # Invalid role title (special chars) -> 422
    res = client.post("/api/v1/placements/requirements", json={
        "company_name": "Valid Company",
        "role_title": "$$$$$$***",
        "min_cgpa": 7.0,
    }, headers=headers)
    assert res.status_code == 422

    # Invalid CGPA (> 10) -> 422
    res = client.post("/api/v1/placements/requirements", json={
        "company_name": "Valid Company",
        "role_title": "Software Engineer",
        "min_cgpa": 11.0,
    }, headers=headers)
    assert res.status_code == 422

    # Invalid required skill (non-MVP) -> 422
    res = client.post("/api/v1/placements/requirements", json={
        "company_name": "Valid Company",
        "role_title": "Software Engineer",
        "min_cgpa": 7.0,
        "required_skills": {"Kubernetes": "SKILL_VERIFIED"}
    }, headers=headers)
    assert res.status_code == 422


# =========================================================================
# 4. DIRECTORY QUERY FILTER VALIDATION
# =========================================================================

def test_directory_filter_bounds(client, clean_db, coordinator_token):
    """Verify coordinator directory filters enforce bounds."""
    headers = {"Authorization": f"Bearer {coordinator_token}"}

    # Search exceeding 100 chars -> 422
    long_search = "A" * 101
    res = client.get(f"/api/v1/students?search={long_search}", headers=headers)
    assert res.status_code == 422

    # Min CGPA exceeding 10.0 -> 422
    res = client.get("/api/v1/students?min_cgpa=11.0", headers=headers)
    assert res.status_code == 422

    # Valid search -> 200
    res = client.get("/api/v1/students?search=John&branch=CSE&min_cgpa=7.5", headers=headers)
    assert res.status_code == 200
