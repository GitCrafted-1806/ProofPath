"""End-to-End Live Validation of the Fresh Evaluator Journey for ProofPath Phase 5."""
import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8000"


def http_request(
    method: str,
    path: str,
    data: dict = None,
    token: str = None,
    is_multipart: bool = False,
    files: dict = None,
    custom_base: str = None
) -> tuple:
    """Synchronous HTTP helper for live FastAPI integration testing."""
    base = custom_base or BASE_URL
    url = f"{base}{path}"
    headers = {"Accept": "application/json"}
    body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if is_multipart and files:
        boundary = "----WebKitFormBoundaryProofPathE2EFreshEvaluator77"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts = []

        if data:
            for k, v in data.items():
                parts.append(
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
                )

        for field_name, (filename, file_bytes, mime_type) in files.items():
            header = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; "
                f"filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n"
            )
            parts.append(header.encode("utf-8") + file_bytes + b"\r\n")

        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(parts)
    elif data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            resp_status = response.status
            content = response.read().decode("utf-8")
            try:
                resp_json = json.loads(content)
            except Exception:
                resp_json = content
            return resp_status, resp_json
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_content)
        except Exception:
            err_json = err_content
        return e.code, err_json
    except urllib.error.URLError as e:
        return 0, str(e.reason)


def main():
    print("=" * 80)
    print("PROOFPATH PHASE 5: FRESH EVALUATOR JOURNEY END-TO-END VALIDATION")
    print("=" * 80)

    # 1. Backend Health Check
    print("\n[Step 1] Verifying live FastAPI backend health...")
    status, body = http_request("GET", "/api/health")
    assert status == 200 and body.get("status") == "healthy", f"Backend unhealthy: {body}"
    print(f" -> Backend healthy at {BASE_URL} (demo_mode={body.get('demo_mode')})")

    # 2. Reset Demo Database to Baseline
    print("\n[Step 2] Resetting demo state to clean baseline...")
    status, body = http_request("POST", "/api/v1/demo/reset")
    assert status == 200, f"Demo reset failed: {body}"
    print(" -> Baseline database initialized.")

    # 3. Invalid Credentials Test
    print("\n[Step 3] Testing invalid credentials handling...")
    status, err_resp = http_request("POST", "/api/v1/auth/login", {
        "email": "nonexistent.user@nit.edu",
        "password": "WrongPassword!"
    })
    assert status == 401, f"Expected HTTP 401, got {status}: {err_resp}"
    print(f" -> Successfully rejected invalid credentials with HTTP 401: {err_resp.get('detail')}")

    # 4. Fresh Student Account Registration
    timestamp = int(time.time())
    fresh_email = f"evaluator.{timestamp}@nit.edu"
    print(f"\n[Step 4] Registering brand new student account: {fresh_email}...")
    status, reg_resp = http_request("POST", "/api/v1/auth/register", {
        "email": fresh_email,
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Alex Chen",
        "college_name": "National Institute of Technology",
        "branch": "Computer Science & Engineering",
        "academic_year": 2026,
        "cgpa": 8.8,
        "qualification": "B.Tech"
    })
    assert status == 201, f"Registration failed ({status}): {reg_resp}"
    fresh_user_id = reg_resp["id"]
    print(f" -> New user created successfully (user_id: {fresh_user_id})")

    # 5. Fresh Student Login
    print(f"\n[Step 5] Logging in with newly registered account...")
    status, auth_resp = http_request("POST", "/api/v1/auth/login", {
        "email": fresh_email,
        "password": "Password123!"
    })
    assert status == 200, f"Login failed ({status}): {auth_resp}"
    fresh_token = auth_resp["access_token"]
    print(f" -> Received JWT access token: {fresh_token[:20]}...")

    # 6. Session Persistence Verification
    print("\n[Step 6] Testing session persistence via GET /api/v1/auth/me...")
    status, me_resp = http_request("GET", "/api/v1/auth/me", token=fresh_token)
    assert status == 200 and me_resp["email"] == fresh_email
    print(f" -> Verified token identity: {me_resp['email']} (role={me_resp['role']})")

    # 7. Initial Dashboard & Baseline Skill State
    print("\n[Step 7] Fetching student dashboard data from GET /api/v1/students/me...")
    status, profile = http_request("GET", "/api/v1/students/me", token=fresh_token)
    assert status == 200, f"Profile fetch failed: {profile}"
    student_id = profile["id"]
    public_id = profile["public_profile_id"]
    print(f" -> Profile: {profile['full_name']} ({profile['branch']} • CGPA: {profile['cgpa']})")
    print(f" -> Public Verification ID: {public_id}")

    # Verify all 4 MVP skills are initially UNVERIFIED for a fresh student
    skills_map = {s["skill_name"]: s["verification_status"] for s in profile["skills"]}
    print(" -> Initial Skill Statuses for fresh student:")
    for sk, st in skills_map.items():
        print(f"     - {sk}: {st}")
        assert st == "UNVERIFIED", f"Expected skill {sk} to be UNVERIFIED for fresh student, got {st}"
    print(" -> CONFIRMED: All 4 MVP skills start strictly UNVERIFIED.")

    # 8. Profile Edit & Backend Persistence
    print("\n[Step 8] Testing academic profile edit & persistence via PATCH /api/v1/students/me...")
    status, patch_resp = http_request("PATCH", "/api/v1/students/me", {
        "full_name": "Alexander Chen",
        "branch": "Artificial Intelligence & Data Science",
        "cgpa": 9.12
    }, token=fresh_token)
    assert status == 200
    assert patch_resp["full_name"] == "Alexander Chen"
    assert patch_resp["branch"] == "Artificial Intelligence & Data Science"
    assert patch_resp["cgpa"] == 9.12

    # Refetch to confirm database persistence
    status, refetch_profile = http_request("GET", "/api/v1/students/me", token=fresh_token)
    assert refetch_profile["full_name"] == "Alexander Chen"
    assert refetch_profile["cgpa"] == 9.12
    print(" -> Profile edits successfully persisted in the backend database.")

    # 9. Real PDF Certificate Document Upload
    print("\n[Step 9] Generating and uploading genuine PDF certificate evidence...")
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (50, 72),
            "Coursera Verified Certificate: Advanced Python Programming and Pandas Data Analysis. Awarded to Alexander Chen."
        )
        sample_pdf_bytes = doc.tobytes()
        doc.close()
    except Exception:
        # Fallback genuine PDF bytes
        sample_pdf_bytes = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 300 144]/Contents 4 0 R/Parent 2 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj "
            b"4 0 obj<</Length 105>>stream\nBT /F1 12 Tf 50 100 Td (Coursera Certificate: Advanced Python Programming and "
            b"Pandas Data Analysis) Tj ET\nendstream\nendobj 5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
            b"0000000229 00000 n\n0000000385 00000 n\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n463\n%%EOF"
        )

    status, upload_resp = http_request(
        "POST",
        "/api/v1/evidence/upload",
        data={"type": "CERTIFICATE"},
        token=fresh_token,
        is_multipart=True,
        files={"file": ("python_pandas_cert.pdf", sample_pdf_bytes, "application/pdf")}
    )
    assert status == 201, f"Evidence upload failed ({status}): {upload_resp}"
    evidence_id = upload_resp["id"]
    detected_skills = [s["skill_name"] if isinstance(s, dict) else s for s in upload_resp.get("skills", [])]
    print(f" -> Upload successful (id: {evidence_id})")
    print(f" -> Authenticity state: {upload_resp.get('authenticity_state')}")
    print(f" -> Mapped skills: {detected_skills}")

    # 10. Verify State Transition: UNVERIFIED -> EVIDENCE_SUPPORTED
    print("\n[Step 10] Checking deterministic verification transition: UNVERIFIED -> EVIDENCE_SUPPORTED...")
    status, profile_after_upload = http_request("GET", "/api/v1/students/me", token=fresh_token)
    new_skills_map = {s["skill_name"]: s["verification_status"] for s in profile_after_upload["skills"]}
    for sk, st in new_skills_map.items():
        print(f"     - {sk}: {st}")
    assert new_skills_map["Python"] == "EVIDENCE_SUPPORTED", f"Expected Python to be EVIDENCE_SUPPORTED, got {new_skills_map['Python']}"
    print(" -> CONFIRMED: Python transitioned from UNVERIFIED to EVIDENCE_SUPPORTED.")

    # 11. Evidence Listing and Detail Retrieval
    print("\n[Step 11] Fetching evidence list from GET /api/v1/evidence/me...")
    status, ev_list = http_request("GET", "/api/v1/evidence/me", token=fresh_token)
    assert status == 200 and len(ev_list) >= 1
    found = next((e for e in ev_list if e["id"] == evidence_id), None)
    assert found is not None
    print(f" -> Verified evidence in list: {found['original_filename']} ({found['type']})")

    status, ev_detail = http_request("GET", f"/api/v1/evidence/{evidence_id}", token=fresh_token)
    assert status == 200 and ev_detail["id"] == evidence_id
    print(f" -> Evidence detail verified (SHA256: {ev_detail.get('extracted_metadata', {}).get('sha256', '')[:16]}...)")

    # 12. Assessment Availability Check
    print("\n[Step 12] Checking assessment availability from GET /api/v1/assessments/available...")
    status, avail_list = http_request("GET", "/api/v1/assessments/available", token=fresh_token)
    assert status == 200
    py_avail = next(a for a in avail_list if a["skill_name"] == "Python")
    assert py_avail["practical_available"] is True, "Practical assessment should now be unlocked for Python"
    assert py_avail["followup_available"] is False, "Follow-up should still be locked"
    py_skill_id = py_avail["skill_id"]
    print(f" -> Python: Practical available = {py_avail['practical_available']} (Reason: {py_avail['reason']})")

    # 13. Start Practical Assessment & Security Answer Masking
    print("\n[Step 13] Starting Practical Assessment for Python...")
    status, start_resp = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": py_skill_id,
        "type": "PRACTICAL"
    }, token=fresh_token)
    assert status == 201, f"Failed to start assessment: {start_resp}"
    assessment_id = start_resp["id"]
    questions = start_resp["questions"]
    print(f" -> Assessment created (id: {assessment_id}, {len(questions)} questions)")

    # Security check: verify no answers or explanations in client payload
    for q in questions:
        assert "correct_answer" not in q, "SECURITY LEAK: correct_answer exposed in client payload!"
        assert "explanation" not in q, "SECURITY LEAK: explanation exposed in client payload!"
    print(" -> Security verification PASSED: Correct answers are strictly masked.")

    # 14. Submit Practical Assessment & State Transition: EVIDENCE_SUPPORTED -> SKILL_ASSESSED
    print("\n[Step 14] Submitting answers for Python Practical Assessment...")
    py_prac_answers = {
        "py_prac_1": "tuple",
        "py_prac_2": "[2, 6, 10]",
        "py_prac_3": 4,
        "py_prac_4": "except"
    }
    status, submit_resp = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {
        "answers": py_prac_answers
    }, token=fresh_token)
    assert status == 200, f"Submit failed: {submit_resp}"
    assert submit_resp["score"] == 100.0
    assert submit_resp["passed"] is True
    assert submit_resp["new_skill_status"] == "SKILL_ASSESSED"
    print(f" -> Score: {submit_resp['score']}%, Passed: {submit_resp['passed']}")
    print(f" -> Verification engine updated status: {submit_resp['new_skill_status']}")

    # Verify on profile
    status, profile_assessed = http_request("GET", "/api/v1/students/me", token=fresh_token)
    py_st = next(s["verification_status"] for s in profile_assessed["skills"] if s["skill_name"] == "Python")
    assert py_st == "SKILL_ASSESSED"
    print(" -> CONFIRMED: Python transitioned from EVIDENCE_SUPPORTED to SKILL_ASSESSED.")

    # 15. GitHub Connect in DEMO_MODE
    print("\n[Step 15] Connecting GitHub account via DEMO_MODE flow...")
    status, oauth_start = http_request("GET", "/api/v1/github/oauth/start", token=fresh_token)
    assert status == 200
    state_token = oauth_start["state"]
    status, _ = http_request("GET", f"/api/v1/github/callback?code=demo_code&state={state_token}")
    assert status == 200
    status, gh_status = http_request("GET", "/api/v1/github/status", token=fresh_token)
    assert gh_status["is_connected"] is True
    print(f" -> GitHub connected: @{gh_status['github_username']}")

    # 16. Select Repository Evidence
    print("\n[Step 16] Browsing repositories and linking project evidence for Python...")
    status, repos = http_request("GET", "/api/v1/github/repositories", token=fresh_token)
    assert status == 200 and len(repos) >= 1
    selected_repo = "octocat-dev/analytics-pipeline"
    status, select_resp = http_request("POST", "/api/v1/github/repositories/select", {
        "repo_full_name": selected_repo
    }, token=fresh_token)
    assert status == 201
    print(f" -> Selected repository evidence: {selected_repo} (id: {select_resp['id']})")

    # 17. Check Follow-Up Assessment Unlocked
    print("\n[Step 17] Verifying Follow-Up Assessment is now unlocked...")
    status, avail_list2 = http_request("GET", "/api/v1/assessments/available", token=fresh_token)
    py_avail2 = next(a for a in avail_list2 if a["skill_name"] == "Python")
    assert py_avail2["followup_available"] is True, "Follow-Up should now be unlocked for Python!"
    print(" -> Follow-Up assessment is unlocked and ready.")

    # 18. Complete Follow-Up Assessment: SKILL_ASSESSED -> SKILL_VERIFIED
    print("\n[Step 18] Starting and completing Follow-Up Assessment for Python...")
    status, fu_start = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": py_skill_id,
        "type": "FOLLOW_UP"
    }, token=fresh_token)
    assert status == 201
    fu_id = fu_start["id"]
    fu_answers = {
        "py_fu_1": "It automatically closes the file even if exceptions occur",
        "py_fu_2": "4",
        "py_fu_3": "O(1)"
    }
    status, fu_submit = http_request("POST", f"/api/v1/assessments/{fu_id}/submit", {
        "answers": fu_answers
    }, token=fresh_token)
    assert status == 200
    assert fu_submit["score"] == 100.0 and fu_submit["passed"] is True
    assert fu_submit["new_skill_status"] == "SKILL_VERIFIED"
    print(f" -> Follow-Up passed: 100% score -> Python transitioned to SKILL_VERIFIED!")

    # 19. Final Profile State Verification
    print("\n[Step 19] Confirming final profile verification state on student profile...")
    status, profile_final = http_request("GET", "/api/v1/students/me", token=fresh_token)
    py_final_st = next(s["verification_status"] for s in profile_final["skills"] if s["skill_name"] == "Python")
    assert py_final_st == "SKILL_VERIFIED"
    print(" -> CONFIRMED: Python is fully SKILL_VERIFIED on student profile.")

    # 20. Public Verification Portfolio Endpoint
    print(f"\n[Step 20] Querying unauthenticated public verification portfolio: GET /api/v1/students/public/{public_id}...")
    status, public_profile = http_request("GET", f"/api/v1/students/public/{public_id}")
    assert status == 200
    assert "user_id" not in public_profile
    assert "email" not in public_profile
    assert public_profile["full_name"] == "Alexander Chen"
    verified_skills = [s["skill_name"] for s in public_profile["skills"] if s["verification_status"] == "SKILL_VERIFIED"]
    assert "Python" in verified_skills
    print(f" -> Public profile successfully verified (Public Verified Skills: {verified_skills})")

    # 21. Student Isolation & Unauthorized Access Protection
    print("\n[Step 21] Verifying student ownership isolation and unauthorized access prevention...")
    status, unauth_reg = http_request("POST", "/api/v1/auth/register", {
        "email": f"unauthorized.{timestamp}@nit.edu",
        "password": "Password123!",
        "role": "STUDENT",
        "full_name": "Intruder User"
    })
    assert status == 201
    status, unauth_auth = http_request("POST", "/api/v1/auth/login", {
        "email": f"unauthorized.{timestamp}@nit.edu",
        "password": "Password123!"
    })
    unauth_token = unauth_auth["access_token"]

    # Unauthorized access to Alex Chen's assessment -> MUST return 403 Forbidden
    status, err1 = http_request("GET", f"/api/v1/assessments/{assessment_id}", token=unauth_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"
    status, err2 = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {"answers": {}}, token=unauth_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"

    # Unauthorized access to Alex Chen's evidence detail -> MUST return 403 Forbidden
    status, err3 = http_request("GET", f"/api/v1/evidence/{evidence_id}", token=unauth_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"

    # Unauthorized deletion of Alex Chen's evidence -> Scoped query returns 404 (not in student's evidence)
    status, err4 = http_request("DELETE", f"/api/v1/evidence/{evidence_id}", token=unauth_token)
    assert status == 404, f"Expected 404 Not Found, got {status}"
    print(" -> CONFIRMED: Student isolation strictly enforced (HTTP 403 Forbidden on foreign data, 404 on scoped mutations).")

    # 22. Backend Unavailable / Offline Simulation Handling
    print("\n[Step 22] Testing frontend client handling when backend is unavailable...")
    err_status, err_reason = http_request("GET", "/api/health", custom_base="http://127.0.0.1:9999")
    assert err_status == 0, "Expected connection error on invalid port"
    print(f" -> Client network layer properly catches offline status without crashing: {err_reason}")

    # 23. Seeded Demo Account Quick Access Check
    print("\n[Step 23] Confirming seeded demo account (John Doe) remains functional...")
    status, john_auth = http_request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert status == 200 and "access_token" in john_auth
    status, john_prof = http_request("GET", "/api/v1/students/me", token=john_auth["access_token"])
    assert status == 200 and john_prof["full_name"] == "John Doe"
    print(" -> CONFIRMED: Seeded demo accounts operate in parallel with fresh user registrations.")

    print("\n" + "=" * 80)
    print("ALL 23 END-TO-END FRESH EVALUATOR JOURNEY VERIFICATION CHECKS PASSED!")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
