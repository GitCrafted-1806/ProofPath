"""End-to-end integration validation script for ProofPath Phase 5 Student Mobile Application."""
import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def http_request(method: str, path: str, data: dict = None, token: str = None, is_multipart: bool = False, files: dict = None) -> tuple:
    """Synchronous HTTP helper for live FastAPI integration testing."""
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if is_multipart and files:
        boundary = "----WebKitFormBoundaryProofPath7MA4YWxkTrZu0gW"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts = []

        # Add fields
        if data:
            for k, v in data.items():
                parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))

        # Add files
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


def main():
    print("=" * 75)
    print("ProofPath Phase 5: Student Mobile Application End-to-End Workflow Verification")
    print("=" * 75)

    # 1. Health Check
    print("\n[Step 1] Verifying FastAPI backend health...")
    status, body = http_request("GET", "/api/health")
    assert status == 200 and body.get("status") == "healthy", f"Backend unhealthy: {body}"
    print(f" -> Backend healthy at {BASE_URL} (demo_mode={body.get('demo_mode')})")

    # 2. Reset Demo Database
    print("\n[Step 2] Resetting demo state to baseline...")
    status, body = http_request("POST", "/api/v1/demo/reset")
    assert status == 200, f"Demo reset failed: {body}"
    print(" -> Demo database reset complete.")

    # 3. Student Login (John Doe)
    print("\n[Step 3] Authenticating as John Doe via mobile auth client...")
    status, auth_data = http_request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Login failed: {auth_data}"
    john_token = auth_data["access_token"]
    print(f" -> Received access_token: {john_token[:20]}...")

    # 4. Dashboard Data Retrieval
    print("\n[Step 4] Fetching student dashboard data from GET /api/v1/students/me...")
    status, profile = http_request("GET", "/api/v1/students/me", token=john_token)
    assert status == 200, f"Failed to fetch profile: {profile}"
    john_profile_id = profile["id"]
    public_id = profile["public_profile_id"]
    print(f" -> Student: {profile['full_name']} ({profile['branch']} • CGPA: {profile['cgpa']})")
    print(f" -> Public Verification ID: {public_id}")

    # 5. Validate Baseline Skill States
    print("\n[Step 5] Checking baseline MVP skills verification statuses...")
    skill_map = {s["skill_name"]: s["verification_status"] for s in profile["skills"]}
    for name, st in skill_map.items():
        print(f"    - {name}: {st}")
    assert skill_map["Python"] == "SKILL_VERIFIED", "Expected Python to be SKILL_VERIFIED"
    assert skill_map["Pandas"] == "SKILL_ASSESSED", "Expected Pandas to be SKILL_ASSESSED"
    assert skill_map["Matplotlib"] == "EVIDENCE_SUPPORTED", "Expected Matplotlib to be EVIDENCE_SUPPORTED"
    assert skill_map["Git/GitHub"] == "EVIDENCE_SUPPORTED", "Expected Git/GitHub to be EVIDENCE_SUPPORTED"
    print(" -> All 4 MVP skill baseline statuses verified.")

    # 6. Check Available Assessments
    print("\n[Step 6] Querying assessment availability from GET /api/v1/assessments/available...")
    status, avail = http_request("GET", "/api/v1/assessments/available", token=john_token)
    assert status == 200, f"Failed to get available assessments: {avail}"
    mpl_avail = next(a for a in avail if a["skill_name"] == "Matplotlib")
    assert mpl_avail["practical_available"] is True, "Practical assessment should be available for Matplotlib"
    assert mpl_avail["followup_available"] is False, "Follow-up should not be available before practical passes"
    mpl_skill_id = mpl_avail["skill_id"]
    print(f" -> Matplotlib: Practical Available = {mpl_avail['practical_available']} (Reason: {mpl_avail['reason']})")

    # 7. Start Practical Assessment
    print("\n[Step 7] Starting Practical Assessment for Matplotlib...")
    status, start_resp = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": mpl_skill_id,
        "type": "PRACTICAL"
    }, token=john_token)
    assert status == 201, f"Failed to start assessment: {start_resp}"
    assessment_id = start_resp["id"]
    questions = start_resp["questions"]
    print(f" -> Assessment ID: {assessment_id}, Questions: {len(questions)}")

    # 8. Security Question Masking Verification
    print("\n[Step 8] Verifying security question masking (answers MUST NOT be leaked)...")
    for q in questions:
        assert "correct_answer" not in q, "SECURITY LEAK: correct_answer exposed!"
        assert "explanation" not in q, "SECURITY LEAK: explanation exposed!"
    print(" -> Question security masking PASSED.")

    # 9. Submit Answers for Practical Assessment
    print("\n[Step 9] Submitting answers for Matplotlib Practical Assessment...")
    answers = {
        "mpl_prac_1": "matplotlib.pyplot",
        "mpl_prac_2": "4",
        "mpl_prac_3": 12,
        "mpl_prac_4": "plt.show()"
    }
    status, submit_resp = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {
        "answers": answers
    }, token=john_token)
    assert status == 200, f"Submission failed: {submit_resp}"
    assert submit_resp["score"] == 100.0, f"Expected 100%, got {submit_resp['score']}"
    assert submit_resp["passed"] is True
    assert submit_resp["new_skill_status"] == "SKILL_ASSESSED"
    print(f" -> Scored: {submit_resp['score']}%, Passed: {submit_resp['passed']}")
    print(f" -> Verification engine updated status: {submit_resp['new_skill_status']}")

    # 10. Verify Updated Profile Reflects SKILL_ASSESSED
    print("\n[Step 10] Verifying Matplotlib status is now SKILL_ASSESSED on student profile...")
    status, profile2 = http_request("GET", "/api/v1/students/me", token=john_token)
    mpl_new_st = next(s["verification_status"] for s in profile2["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_new_st == "SKILL_ASSESSED", f"Expected SKILL_ASSESSED, got {mpl_new_st}"
    print(" -> Profile confirmed in SKILL_ASSESSED state.")

    # 10b. Evidence Upload via Mobile Client
    print("\n[Step 10b] Testing mobile document evidence upload (PDF certificate)...")
    try:
        import fitz
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((50, 72), "Coursera Verified Certificate: Advanced Python and Machine Learning")
        sample_pdf_bytes = doc.tobytes()
        doc.close()
    except Exception:
        # Minimal valid PDF fallback
        sample_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 300 144]/Contents 4 0 R/Parent 2 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj 4 0 obj<</Length 70>>stream\nBT /F1 12 Tf 50 100 Td (Coursera Certificate in Advanced Python Specialization) Tj ET\nendstream\nendobj 5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000229 00000 n\n0000000350 00000 n\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n428\n%%EOF"

    status, upload_resp = http_request(
        "POST",
        "/api/v1/evidence/upload",
        data={"type": "CERTIFICATE"},
        token=john_token,
        is_multipart=True,
        files={"file": ("python_specialization.pdf", sample_pdf_bytes, "application/pdf")}
    )
    assert status == 201, f"Evidence upload failed ({status}): {upload_resp}"
    uploaded_ev_id = upload_resp["id"]
    print(f" -> Successfully uploaded certificate (id: {uploaded_ev_id})")
    print(f" -> Detected skills: {[s['skill_name'] for s in upload_resp.get('skills', [])]}")
    print(f" -> Authenticity state: {upload_resp.get('authenticity_state')}")

    # 10c. Fetch Student Evidence List & Detail
    print("\n[Step 10c] Fetching student evidence items from GET /api/v1/evidence/me...")
    status, ev_list = http_request("GET", "/api/v1/evidence/me", token=john_token)
    assert status == 200, f"Failed to list evidence: {ev_list}"
    matching = [e for e in ev_list if e["id"] == uploaded_ev_id]
    assert len(matching) == 1, "Uploaded evidence not found in /api/v1/evidence/me"
    print(f" -> Total student evidence items: {len(ev_list)} (uploaded item verified in list)")

    status, ev_detail = http_request("GET", f"/api/v1/evidence/{uploaded_ev_id}", token=john_token)
    assert status == 200 and ev_detail["id"] == uploaded_ev_id
    print(f" -> Evidence detail retrieved: original_filename={ev_detail.get('original_filename')}")

    # 11. Connect GitHub (DEMO_MODE flow)
    print("\n[Step 11] Connecting GitHub account via DEMO_MODE flow...")
    status, oauth_start = http_request("GET", "/api/v1/github/oauth/start", token=john_token)
    assert status == 200
    state = oauth_start["state"]
    status, _ = http_request("GET", f"/api/v1/github/callback?code=demo_code&state={state}")
    assert status == 200
    status, gh_status = http_request("GET", "/api/v1/github/status", token=john_token)
    assert gh_status["is_connected"] is True
    print(f" -> GitHub connected: @{gh_status['github_username']}")

    # 12. Select Repository Evidence
    print("\n[Step 12] Browsing repositories and selecting project evidence for Matplotlib...")
    status, repos = http_request("GET", "/api/v1/github/repositories", token=john_token)
    assert status == 200 and len(repos) >= 1
    selected_repo = "octocat-dev/analytics-pipeline"
    status, select_resp = http_request("POST", "/api/v1/github/repositories/select", {
        "repo_full_name": selected_repo
    }, token=john_token)
    assert status == 201
    print(f" -> Selected repository evidence: {selected_repo} (id: {select_resp['id']})")

    # 13. Check Follow-Up Assessment Availability
    print("\n[Step 13] Checking follow-up assessment availability for Matplotlib...")
    status, avail2 = http_request("GET", "/api/v1/assessments/available", token=john_token)
    mpl_avail2 = next(a for a in avail2 if a["skill_name"] == "Matplotlib")
    assert mpl_avail2["followup_available"] is True, "Follow-up should now be available!"
    print(" -> Follow-Up assessment is now unlocked and available.")

    # 14. Start and Submit Follow-Up Assessment
    print("\n[Step 14] Starting and completing Follow-Up Assessment for Matplotlib...")
    status, fu_start = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": mpl_skill_id,
        "type": "FOLLOW_UP"
    }, token=john_token)
    assert status == 201
    fu_id = fu_start["id"]
    fu_answers = {
        "mpl_fu_1": "plt.savefig()",
        "mpl_fu_2": "cleared",
        "mpl_fu_3": "The label for the x-axis"
    }
    status, fu_submit = http_request("POST", f"/api/v1/assessments/{fu_id}/submit", {
        "answers": fu_answers
    }, token=john_token)
    assert status == 200
    assert fu_submit["score"] == 100.0 and fu_submit["passed"] is True
    assert fu_submit["new_skill_status"] == "SKILL_VERIFIED"
    print(f" -> Follow-Up passed: 100.0% score -> Matplotlib transitioned to SKILL_VERIFIED!")

    # 15. Final Profile Verification State
    print("\n[Step 15] Confirming final profile verification states...")
    status, profile3 = http_request("GET", "/api/v1/students/me", token=john_token)
    mpl_final = next(s["verification_status"] for s in profile3["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_final == "SKILL_VERIFIED"
    print(" -> Matplotlib is now fully SKILL_VERIFIED on student profile.")

    # 16. Public Verification Resume View
    print("\n[Step 16] Querying public verification resume endpoint GET /api/v1/students/public/{public_id}...")
    status, public_profile = http_request("GET", f"/api/v1/students/public/{public_id}")
    assert status == 200
    assert "user_id" not in public_profile
    assert "email" not in public_profile
    assert public_profile["full_name"] == "John Doe"
    verified_skills = [s["skill_name"] for s in public_profile["skills"] if s["verification_status"] == "SKILL_VERIFIED"]
    print(f" -> Public profile successfully verified (Verified skills: {verified_skills})")

    # 17. Profile Editing & Backend Persistence
    print("\n[Step 17] Testing academic profile edit & persistence via PATCH /api/v1/students/me...")
    status, patch_resp = http_request("PATCH", "/api/v1/students/me", {
        "full_name": "Johnathon Doe",
        "cgpa": 9.15,
        "branch": "Advanced Computing & AI"
    }, token=john_token)
    assert status == 200
    assert patch_resp["full_name"] == "Johnathon Doe"
    assert patch_resp["cgpa"] == 9.15
    assert patch_resp["branch"] == "Advanced Computing & AI"

    # Verify persistence by refetching
    status, refetch_prof = http_request("GET", "/api/v1/students/me", token=john_token)
    assert refetch_prof["full_name"] == "Johnathon Doe"
    assert refetch_prof["cgpa"] == 9.15
    print(" -> Profile edits successfully persisted in backend database.")

    # 18. Student Ownership Isolation Check
    print("\n[Step 18] Verifying student ownership isolation (Jane Smith cannot access John's data)...")
    status, jane_auth = http_request("POST", "/api/v1/auth/login", {
        "email": "jane.smith@nit.edu",
        "password": "Password123!"
    })
    jane_token = jane_auth["access_token"]
    status, err = http_request("GET", f"/api/v1/assessments/{assessment_id}", token=jane_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"
    status, err2 = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {"answers": {}}, token=jane_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"
    print(" -> Ownership isolation strictly confirmed (HTTP 403 Forbidden).")

    print("\n" + "=" * 75)
    print("ALL 18 END-TO-END MOBILE WORKFLOW VERIFICATION CHECKS PASSED!")
    print("=" * 75)
    sys.exit(0)


if __name__ == "__main__":
    main()
