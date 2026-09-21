import io
import fitz
from PIL import Image
import pytest


def get_authenticated_student_token(client, email="student_upload@example.com"):
    """Helper to create and authenticate a student user."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Test Student",
        "cgpa": 8.0
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return login_res.json()["access_token"]


def get_authenticated_coordinator_token(client, email="coord_upload@example.com"):
    """Helper to create and authenticate a coordinator user."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "PLACEMENT_COORDINATOR"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return login_res.json()["access_token"]


def create_sample_pdf(text: str = "Certificate in Python and Pandas Programming") -> bytes:
    """Create a minimal genuine PDF in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_sample_image(img_format: str = "PNG") -> bytes:
    """Create a minimal genuine image in memory using PIL."""
    img = Image.new("RGB", (120, 60), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format=img_format)
    return buf.getvalue()


def test_upload_valid_pdf_success(client):
    """Test successful upload of a genuine digital PDF certificate."""
    token = get_authenticated_student_token(client, "student_pdf@example.com")
    pdf_content = create_sample_pdf("Coursera Verified Certificate: Python for Data Science. Awarded to Test Student.")

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("certificate.pdf", pdf_content, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "CERTIFICATE"
    assert data["authenticity_state"] == "SUBMITTED"
    assert "Python" in data["mapped_skills"]
    assert data["extracted_metadata"]["issuer"] == "Coursera"
    assert data["extracted_metadata"]["file_size"] == len(pdf_content)


def test_upload_valid_png_success(client):
    """Test successful upload of a valid PNG project document."""
    token = get_authenticated_student_token(client, "student_png@example.com")
    png_content = create_sample_image("PNG")

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("diagram.png", png_content, "image/png")},
        data={"type": "PROJECT_DOCUMENT"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "PROJECT_DOCUMENT"
    assert data["authenticity_state"] == "SUBMITTED"
    assert data["extracted_metadata"]["mime_type"] == "image/png"


def test_upload_valid_jpeg_success(client):
    """Test successful upload of a valid JPEG image."""
    token = get_authenticated_student_token(client, "student_jpg@example.com")
    jpeg_content = create_sample_image("JPEG")

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("scan.jpg", jpeg_content, "image/jpeg")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "CERTIFICATE"
    assert data["authenticity_state"] == "SUBMITTED"
    assert data["extracted_metadata"]["mime_type"] == "image/jpeg"


def test_upload_file_exceeding_5mb_rejected(client):
    """Test that file exceeding 5 MB limit is aborted with HTTP 413."""
    token = get_authenticated_student_token(client, "student_large@example.com")
    # Header + 5.1 MB of padding
    oversized_content = b"%PDF-1.4\n" + (b"0" * (5 * 1024 * 1024 + 1024))

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("oversized.pdf", oversized_content, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 413
    assert "exceeds maximum allowed upload size" in response.json()["detail"]


def test_upload_disallowed_extension_rejected(client):
    """Test that disallowed file extensions are rejected with HTTP 400."""
    token = get_authenticated_student_token(client, "student_ext@example.com")

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_upload_spoofed_mime_type_rejected(client):
    """Test that file with .pdf extension but invalid magic bytes is rejected."""
    token = get_authenticated_student_token(client, "student_spoof@example.com")

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fake.pdf", b"Hello World Plain Text", "application/pdf")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 400
    assert "signature does not match" in response.json()["detail"]


def test_upload_corrupted_image_rejected(client):
    """Test that corrupted image bytes are rejected by PIL integrity verification."""
    token = get_authenticated_student_token(client, "student_corrupt@example.com")
    corrupted_png = b"\x89PNG\r\n\x1a\n" + b"random_corrupted_garbage_bytes"

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("corrupt.png", corrupted_png, "image/png")},
        data={"type": "PROJECT_DOCUMENT"}
    )

    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"]


def test_upload_github_repo_type_rejected(client):
    """Test that GITHUB_REPO uploads are disallowed in Phase 2."""
    token = get_authenticated_student_token(client, "student_github@example.com")
    pdf_content = create_sample_pdf()

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("repo.pdf", pdf_content, "application/pdf")},
        data={"type": "GITHUB_REPO"}
    )

    assert response.status_code == 400
    assert "GITHUB_REPO" in response.json()["detail"]


def test_unauthenticated_upload_rejected(client):
    """Test that upload without JWT token is rejected with HTTP 401."""
    pdf_content = create_sample_pdf()

    response = client.post(
        "/api/v1/evidence/upload",
        files={"file": ("certificate.pdf", pdf_content, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 401


def test_coordinator_cannot_upload_evidence(client):
    """Test that placement coordinators are forbidden from uploading student evidence."""
    coord_token = get_authenticated_coordinator_token(client, "coord_no_upload@example.com")
    pdf_content = create_sample_pdf()

    response = client.post(
        "/api/v1/evidence/upload",
        headers={"Authorization": f"Bearer {coord_token}"},
        files={"file": ("cert.pdf", pdf_content, "application/pdf")},
        data={"type": "CERTIFICATE"}
    )

    assert response.status_code == 403
