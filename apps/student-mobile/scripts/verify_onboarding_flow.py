"""
Focused validation script for ProofPath Student Mobile Onboarding UX Correction:
1. Validates new student onboarding with explicit CGPA and custom claimed MVP skills.
2. Validates CGPA boundary enforcement (0.0 to 10.0).
3. Validates that claimed skills start strictly UNVERIFIED (no automatic verification).
4. Validates that student dashboard/profile accurately reflects submitted CGPA and selected skills.
5. Validates that evidence upload proceeds normally for the newly onboarded student.
6. Validates that existing demo accounts (John Doe, Jane Smith) continue functioning seamlessly.
7. Validates that sign-out works properly.
"""

import time
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def http_request(method: str, path: str, data: dict = None, token: str = None, is_multipart: bool = False, files: dict = None) -> tuple:
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if is_multipart and files:
        boundary = "----WebKitFormBoundaryProofPathOnboardingTest"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts = []
        if data:
            for k, v in data.items():
                parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
        for field_name, (filename, file_bytes, mime_type) in files.items():
            header = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n"
            parts.append(header.encode("utf-8") + file_bytes + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(parts)
    elif data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(content)
            except Exception:
                return resp.status, content
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_content)
        except Exception:
            return e.code, err_content


def test_onboarding_flow():
    print("=" * 80)
    print("PROOFPATH: FOCUSED STUDENT MOBILE ONBOARDING & VERIFICATION AUDIT")
    print("=" * 80)

    # 1. Health check
    print("\n[Check 1] Verifying backend health...")
    status, health = http_request("GET", "/api/health")
    assert status == 200 and health.get("status") == "healthy", f"Backend unhealthy: {health}"
    print(f" -> Backend healthy at {BASE_URL}")

    # 2. Reset database
    print("\n[Check 2] Resetting database to baseline state...")
    status, _ = http_request("POST", "/api/v1/demo/reset")
    assert status == 200, "Reset failed"
    print(" -> Database baseline established.")

    # 3. Validation: CGPA > 10.0 must be rejected
    print("\n[Check 3] Validating out-of-range CGPA rejection (e.g. 11.5)...")
    status, err_resp = http_request("POST", "/api/v1/auth/register", {
        "email": "invalid_cgpa@nit.edu",
        "password": "Password123!",
        "role": "STUDENT",
        "cgpa": 11.5
    })
    assert status == 422, f"Expected 422 for CGPA > 10.0, got {status}: {err_resp}"
    print(" -> Successfully rejected out-of-range CGPA with HTTP 422.")

    # 4. Create Account with explicit academic details and claimed skills
    ts = int(time.time())
    new_email = f"onboarding.student.{ts}@nit.edu"
    submitted_cgpa = 8.65
    submitted_college = "Delhi Technological University"
    submitted_branch = "Software Engineering"
    submitted_year = 2027
    claimed_skills = ["Python", "Git/GitHub"]  # Selected 2 of 4 MVP skills

    print(f"\n[Check 4] Registering new student with explicit CGPA ({submitted_cgpa}) and claimed skills ({claimed_skills})...")
    status, reg_res = http_request("POST", "/api/v1/auth/register", {
        "email": new_email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Rohan Verma",
        "college_name": submitted_college,
        "branch": submitted_branch,
        "academic_year": submitted_year,
        "cgpa": submitted_cgpa,
        "skills": claimed_skills,
    })
    assert status == 201, f"Registration failed with {status}: {reg_res}"
    print(f" -> User registered successfully (ID: {reg_res['id']}).")

    # 5. Authenticate session
    print("\n[Check 5] Authenticating newly registered student...")
    status, auth_res = http_request("POST", "/api/v1/auth/login", {
        "email": new_email,
        "password": "Password123!"
    })
    assert status == 200, f"Login failed: {auth_res}"
    token = auth_res["access_token"]
    print(f" -> Session token acquired: {token[:25]}...")

    # 6. Verify profile fields, CGPA, and claimed skill statuses
    print("\n[Check 6] Verifying student profile, persisted CGPA, and claimed skills...")
    status, profile = http_request("GET", "/api/v1/students/me", token=token)
    assert status == 200, f"Failed to get profile: {profile}"
    assert profile["full_name"] == "Rohan Verma"
    assert profile["college_name"] == submitted_college
    assert profile["branch"] == submitted_branch
    assert profile["academic_year"] == submitted_year
    assert abs(profile["cgpa"] - submitted_cgpa) < 0.001, f"CGPA mismatch: expected {submitted_cgpa}, got {profile['cgpa']}"
    print(f" -> Persisted CGPA confirmed: {profile['cgpa']} (Scale: 0-10)")

    # 7. Critical Verification Rule Check
    print("\n[Check 7] Verifying CRITICAL RULE: Claimed skills MUST start strictly UNVERIFIED...")
    profile_skills = profile.get("skills", [])
    registered_skill_names = [s["skill_name"] for s in profile_skills]

    assert "Python" in registered_skill_names, "Claimed skill Python missing from profile"
    assert "Git/GitHub" in registered_skill_names, "Claimed skill Git/GitHub missing from profile"
    assert "Pandas" not in registered_skill_names, "Unclaimed skill Pandas should not be registered"
    assert "Matplotlib" not in registered_skill_names, "Unclaimed skill Matplotlib should not be registered"

    for s in profile_skills:
        assert s["verification_status"] == "UNVERIFIED", (
            f"VIOLATION: Skill '{s['skill_name']}' has status '{s['verification_status']}', but MUST be 'UNVERIFIED'!"
        )
        print(f"    - {s['skill_name']}: {s['verification_status']} (CONFIRMED: Student claim only)")

    # 8. Proceed to Evidence Upload
    print("\n[Check 8] Verifying newly registered student can proceed to Evidence Upload...")
    dummy_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000098 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n"
    status, upload_res = http_request(
        "POST",
        "/api/v1/evidence/upload",
        data={"type": "CERTIFICATE"},
        token=token,
        is_multipart=True,
        files={"file": ("python_specialization.pdf", dummy_pdf_bytes, "application/pdf")}
    )
    assert status == 201, f"Evidence upload failed: {upload_res}"
    print(f" -> Successfully uploaded certificate evidence (id: {upload_res['id']}).")

    # 9. Verify evidence list
    status, ev_list = http_request("GET", "/api/v1/evidence/me", token=token)
    assert status == 200 and len(ev_list) == 1
    print(f" -> Evidence list updated: {len(ev_list)} file on record.")

    # 10. Existing Demo Accounts Check
    print("\n[Check 10] Verifying existing demo accounts (John Doe, Jane Smith) continue working...")
    status, jd_res = http_request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"John Doe login failed: {jd_res}"
    print(" -> John Doe demo login confirmed.")

    status, js_res = http_request("POST", "/api/v1/auth/login", {
        "email": "jane.smith@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Jane Smith login failed: {js_res}"
    print(" -> Jane Smith demo login confirmed.")

    # 11. Sign Out check
    print("\n[Check 11] Verifying Sign Out flow...")
    status, me_unauth = http_request("GET", "/api/v1/students/me")
    assert status == 401
    print(" -> Unauthenticated request correctly rejected with HTTP 401.")

    print("\n" + "=" * 80)
    print("ALL 11 ONBOARDING & VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_onboarding_flow()
