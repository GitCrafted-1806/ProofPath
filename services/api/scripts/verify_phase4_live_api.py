"""Live end-to-end API test script for ProofPath Phase 4."""
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def http_request(method: str, path: str, data: dict = None, token: str = None) -> tuple:
    """Helper to perform synchronous HTTP request against live FastAPI server."""
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if data is not None:
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
    print("=" * 70)
    print("ProofPath Phase 4: Live Running API Verification")
    print("=" * 70)

    # 1. Health Check
    print("\n[Step 1] Checking API health endpoint...")
    status, body = http_request("GET", "/api/health")
    print(f" -> GET /api/health: Status {status}")
    assert status == 200, f"Health check failed with status {status}: {body}"
    assert body.get("status") == "healthy", f"Unexpected health status: {body}"
    print("    [PASS] API is healthy and operational.")

    # 2. Reset Demo Database
    print("\n[Step 2] Resetting demo database to initial state...")
    status, body = http_request("POST", "/api/v1/demo/reset")
    print(f" -> POST /api/v1/demo/reset: Status {status}")
    assert status == 200, f"Demo reset failed: {body}"
    print("    [PASS] Demo database successfully reset.")

    # 3. Authenticate as John Doe
    print("\n[Step 3] Logging in as John Doe (Student)...")
    status, body = http_request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    print(f" -> POST /api/v1/auth/login: Status {status}")
    assert status == 200, f"John Doe login failed: {body}"
    john_token = body["access_token"]
    print("    [PASS] Received JWT token for John Doe.")

    # 4. Verify John Doe initial profile states
    print("\n[Step 4] Checking John Doe's baseline skill states...")
    status, profile = http_request("GET", "/api/v1/students/me", token=john_token)
    assert status == 200, f"Failed to retrieve profile: {profile}"
    john_profile_id = profile["id"]
    skill_states = {s["skill_name"]: (s["skill_id"], s["verification_status"]) for s in profile["skills"]}
    print(f" -> Profile ID: {john_profile_id}")
    for name, (s_id, s_status) in skill_states.items():
        print(f"    - {name}: {s_status}")

    assert skill_states["Matplotlib"][1] == "EVIDENCE_SUPPORTED", "Expected Matplotlib to start at EVIDENCE_SUPPORTED"
    mpl_skill_id = skill_states["Matplotlib"][0]
    print("    [PASS] Matplotlib baseline state confirmed as EVIDENCE_SUPPORTED.")

    # 5. Query Assessment Availability
    print("\n[Step 5] Checking assessment availability for John Doe...")
    status, avail_list = http_request("GET", "/api/v1/assessments/available", token=john_token)
    assert status == 200, f"Failed to query available assessments: {avail_list}"
    mpl_avail = next((a for a in avail_list if a["skill_name"] == "Matplotlib"), None)
    assert mpl_avail is not None, "Matplotlib not found in available assessments"
    print(f" -> Matplotlib availability: practical={mpl_avail['practical_available']}, followup={mpl_avail['followup_available']}, reason={mpl_avail['reason']}")
    assert mpl_avail["practical_available"] is True, "Practical assessment should be available"
    assert mpl_avail["followup_available"] is False, "Follow-up should not be available before passing practical"
    print("    [PASS] Deterministic availability flags correctly computed.")

    # 6. Start Practical Assessment for Matplotlib
    print("\n[Step 6] John Doe starts Practical Assessment for Matplotlib...")
    status, start_resp = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": mpl_skill_id,
        "type": "PRACTICAL"
    }, token=john_token)
    print(f" -> POST /api/v1/assessments/start: Status {status}")
    assert status == 201, f"Failed to start assessment: {start_resp}"
    assessment_id = start_resp["id"]
    questions = start_resp["questions"]
    print(f" -> Assessment ID: {assessment_id}, Questions count: {len(questions)}")

    # SECURITY CHECK: Verify answers are NOT in the response
    for q in questions:
        assert "correct_answer" not in q, "SECURITY VIOLATION: correct_answer exposed in take response!"
        assert "explanation" not in q, "SECURITY VIOLATION: explanation exposed in take response!"
    print("    [PASS] Practical assessment created. Security check PASSED (answers masked).")

    # 7. Test GET /{id} on pending assessment
    print("\n[Step 7] Checking GET /api/v1/assessments/{id} on active assessment...")
    status, get_resp = http_request("GET", f"/api/v1/assessments/{assessment_id}", token=john_token)
    assert status == 200
    assert get_resp["status"] == "PENDING"
    for q in get_resp["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q
    print("    [PASS] GET endpoint preserves question masking during PENDING state.")

    # 8. Submit Answers for Practical Assessment
    print("\n[Step 8] John Doe submits answers for Matplotlib Practical Assessment...")
    answers = {
        "mpl_prac_1": "matplotlib.pyplot",
        "mpl_prac_2": "4",
        "mpl_prac_3": 12,
        "mpl_prac_4": "plt.show()"
    }
    status, submit_resp = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {
        "answers": answers
    }, token=john_token)
    print(f" -> POST /api/v1/assessments/{assessment_id}/submit: Status {status}")
    assert status == 200, f"Submission failed: {submit_resp}"
    print(f" -> Score: {submit_resp['score']}%, Passed: {submit_resp['passed']}, Status: {submit_resp['status']}")
    print(f" -> New Skill Status: {submit_resp['new_skill_status']}")
    assert submit_resp["score"] == 100.0, "Expected 100.0% score"
    assert submit_resp["passed"] is True, "Expected passed to be True"
    assert submit_resp["new_skill_status"] == "SKILL_ASSESSED", "Expected transition to SKILL_ASSESSED"
    print("    [PASS] Practical assessment scored deterministically. Skill transitioned to SKILL_ASSESSED.")

    # 9. Verify Student Profile updated
    print("\n[Step 9] Verifying updated skill status on John Doe profile...")
    status, updated_profile = http_request("GET", "/api/v1/students/me", token=john_token)
    mpl_state = next(s for s in updated_profile["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_state["verification_status"] == "SKILL_ASSESSED", f"Expected SKILL_ASSESSED, got {mpl_state['verification_status']}"
    print("    [PASS] Profile confirmed in SKILL_ASSESSED state.")

    # 10. Connect GitHub repository evidence for Matplotlib
    print("\n[Step 10] Connecting GitHub repository evidence for Matplotlib...")
    status, oauth_start = http_request("GET", "/api/v1/github/oauth/start", token=john_token)
    assert status == 200
    state_token = oauth_start["state"]

    # Simulated callback in demo mode
    status, _ = http_request("GET", f"/api/v1/github/callback?code=demo_code&state={state_token}")
    assert status == 200
    print(" -> GitHub OAuth callback completed.")

    # Select repository as evidence
    status, select_resp = http_request("POST", "/api/v1/github/repositories/select", {
        "repo_full_name": "octocat-dev/analytics-pipeline"
    }, token=john_token)
    assert status == 201, f"Selecting repo evidence failed: {select_resp}"
    print(f" -> Selected GitHub repo evidence for Matplotlib: {select_resp['id']}")
    print("    [PASS] GitHub repo evidence registered for Matplotlib.")

    # 11. Check Availability for Follow-up Assessment
    print("\n[Step 11] Checking assessment availability after GitHub repo evidence...")
    status, avail_list2 = http_request("GET", "/api/v1/assessments/available", token=john_token)
    mpl_avail2 = next((a for a in avail_list2 if a["skill_name"] == "Matplotlib"), None)
    print(f" -> Matplotlib availability: practical={mpl_avail2['practical_available']}, followup={mpl_avail2['followup_available']}")
    assert mpl_avail2["followup_available"] is True, "Follow-up should now be available!"
    print("    [PASS] Follow-up assessment is now available.")

    # 12. Start Follow-Up Assessment for Matplotlib
    print("\n[Step 12] John Doe starts Follow-Up Assessment for Matplotlib...")
    status, fu_start = http_request("POST", "/api/v1/assessments/start", {
        "skill_id": mpl_skill_id,
        "type": "FOLLOW_UP"
    }, token=john_token)
    assert status == 201, f"Failed to start follow-up: {fu_start}"
    fu_id = fu_start["id"]
    print(f" -> Follow-up Assessment ID: {fu_id}, Questions: {len(fu_start['questions'])}")

    # 13. Submit Follow-Up Assessment
    print("\n[Step 13] Submitting answers for Follow-Up Assessment...")
    fu_answers = {
        "mpl_fu_1": "plt.savefig()",
        "mpl_fu_2": "cleared",
        "mpl_fu_3": "The label for the x-axis"
    }
    status, fu_submit = http_request("POST", f"/api/v1/assessments/{fu_id}/submit", {
        "answers": fu_answers
    }, token=john_token)
    assert status == 200, f"Follow-up submission failed: {fu_submit}"
    print(f" -> Score: {fu_submit['score']}%, Passed: {fu_submit['passed']}")
    print(f" -> New Skill Status: {fu_submit['new_skill_status']}")
    assert fu_submit["score"] == 100.0
    assert fu_submit["passed"] is True
    assert fu_submit["new_skill_status"] == "SKILL_VERIFIED", f"Expected SKILL_VERIFIED, got {fu_submit['new_skill_status']}"
    print("    [PASS] Matplotlib is now fully SKILL_VERIFIED!")

    # 14. Final Profile Verification
    print("\n[Step 14] Checking final profile verification status...")
    status, final_profile = http_request("GET", "/api/v1/students/me", token=john_token)
    mpl_final = next(s for s in final_profile["skills"] if s["skill_name"] == "Matplotlib")
    assert mpl_final["verification_status"] == "SKILL_VERIFIED"
    print(f" -> Confirmed on student profile: Matplotlib status = {mpl_final['verification_status']}")
    print("    [PASS] Full forward lifecycle completed successfully.")

    # 15. Student Ownership Isolation Check
    print("\n[Step 15] Testing student ownership isolation...")
    status, jane_auth = http_request("POST", "/api/v1/auth/login", {
        "email": "jane.smith@nit.edu",
        "password": "Password123!"
    })
    jane_token = jane_auth["access_token"]

    # Jane tries to GET John's assessment -> 403
    status, err_resp = http_request("GET", f"/api/v1/assessments/{assessment_id}", token=jane_token)
    print(f" -> Jane GET John's assessment: Status {status}")
    assert status == 403, f"Expected 403 Forbidden, got {status}"

    # Jane tries to submit to John's assessment -> 403
    status, err_resp2 = http_request("POST", f"/api/v1/assessments/{assessment_id}/submit", {
        "answers": {}
    }, token=jane_token)
    print(f" -> Jane submit John's assessment: Status {status}")
    assert status == 403, f"Expected 403 Forbidden, got {status}"
    print("    [PASS] Ownership isolation strictly enforced.")

    # 16. Placement Coordinator Audit Inspection
    print("\n[Step 16] Placement Coordinator audits John Doe's assessments...")
    status, coord_auth = http_request("POST", "/api/v1/auth/login", {
        "email": "coordinator@college.edu",
        "password": "Password123!"
    })
    coord_token = coord_auth["access_token"]

    status, audit_history = http_request("GET", f"/api/v1/assessments/student/{john_profile_id}", token=coord_token)
    print(f" -> GET /api/v1/assessments/student/{john_profile_id}: Status {status}")
    assert status == 200, f"Coordinator audit failed: {audit_history}"
    print(f" -> Found {len(audit_history)} assessments in John Doe's history:")
    for a in audit_history:
        print(f"    - {a['skill_name']} ({a['type']}): score={a['score']}%, passed={a['passed']}, status={a['status']}")
    assert len(audit_history) >= 2, "Expected at least practical and follow-up in audit history"
    print("    [PASS] Placement Coordinator audit functionality fully verified.")

    print("\n" + "=" * 70)
    print("ALL 16 LIVE API VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
