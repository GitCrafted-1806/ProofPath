import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(raw.decode("utf-8")), resp.headers
            return resp.status, raw.decode("utf-8", errors="replace"), resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(raw)
        except Exception:
            err_json = raw
        return e.code, err_json, e.headers


def run_live_test():
    print("=== STARTING LIVE PHASE 6 END-TO-END VERIFICATION ===")

    # 1. Reset / ensure demo seed
    print("\n[1] Resetting demo seed...")
    status, res, _ = request("POST", "/api/v1/demo/reset")
    assert status == 200, f"Demo reset failed: {res}"
    print("✓ Demo database ready.")

    # 2. Invalid coordinator login
    print("\n[2] Testing invalid coordinator login...")
    status, res, _ = request("POST", "/api/v1/auth/login", {
        "email": "coordinator@college.edu",
        "password": "WrongPassword999!"
    })
    assert status == 401, f"Expected 401 for invalid login, got {status}: {res}"
    print("✓ Invalid login correctly rejected with 401.")

    # 3. Valid coordinator login
    print("\n[3] Testing live coordinator login...")
    status, res, _ = request("POST", "/api/v1/auth/login", {
        "email": "coordinator@college.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Coordinator login failed: {res}"
    coord_token = res["access_token"]
    print("✓ Live coordinator login succeeded. Received JWT token.")

    # 4. Student login & RBAC rejection
    print("\n[4] Testing student RBAC rejection...")
    status, res, _ = request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Student login failed: {res}"
    student_token = res["access_token"]

    # Student tries coordinator directory
    status, res, _ = request("GET", "/api/v1/students", token=student_token)
    assert status == 403, f"Expected 403 for student accessing directory, got {status}"

    # Student tries creating requirement
    status, res, _ = request("POST", "/api/v1/placements/requirements", {
        "company_name": "TestCorp",
        "role_title": "Intern",
        "min_cgpa": 6.0
    }, token=student_token)
    assert status == 403, f"Expected 403 for student creating requirement, got {status}"
    print("✓ Student RBAC properly rejected with 403 on all coordinator endpoints.")

    # 5. Live Student Directory
    print("\n[5] Testing live student directory query & filtering...")
    status, dir_data, _ = request("GET", "/api/v1/students?search=John", token=coord_token)
    assert status == 200, f"Student directory query failed: {dir_data}"
    assert dir_data["total"] >= 1
    john = dir_data["students"][0]
    john_id = john["id"]
    print(f"✓ Found candidate '{john['full_name']}' ({john['email']}) with CGPA {john['cgpa']}.")

    # 6. Live Student Profile & Evidence Inspection
    print("\n[6] Testing live student profile & evidence inspection...")
    status, prof, _ = request("GET", f"/api/v1/students/{john_id}", token=coord_token)
    assert status == 200, f"Failed to get student profile: {prof}"
    assert prof["full_name"] == "John Doe"

    status, evidences, _ = request("GET", f"/api/v1/evidence/student/{john_id}", token=coord_token)
    assert status == 200, f"Failed to get student evidence: {evidences}"
    assert len(evidences) >= 1
    print(f"✓ Inspected {len(evidences)} evidence files/repos for student {john['full_name']}.")

    # 7. Live Evidence Institutional Verification (Preserve Phase 2 RBAC)
    print("\n[7] Testing evidence institutional verification...")
    cert_evidence = next((e for e in evidences if e["type"] != "GITHUB_REPO"), evidences[0])
    status, ver_res, _ = request("PATCH", f"/api/v1/evidence/{cert_evidence['id']}/verify", {
        "authenticity_state": "INSTITUTION_VERIFIED",
        "remarks": "Verified by Live Test Coordinator"
    }, token=coord_token)
    assert status == 200, f"Evidence verification failed: {ver_res}"
    assert ver_res["authenticity_state"] == "INSTITUTION_VERIFIED"
    print(f"✓ Evidence '{cert_evidence['original_filename']}' verified by coordinator.")

    # 8. Live Placement Requirement Creation
    print("\n[8] Testing placement requirement creation...")
    status, req_data, _ = request("POST", "/api/v1/placements/requirements", {
        "company_name": "Antigravity Systems",
        "role_title": "Full Stack Engineer",
        "min_cgpa": 7.5,
        "eligible_branches": ["CSE", "IT"],
        "required_skills": {
            "Python": "SKILL_VERIFIED"
        }
    }, token=coord_token)
    assert status == 201, f"Requirement creation failed: {req_data}"
    req_id = req_data["id"]
    print(f"✓ Created placement requirement '{req_data['company_name']} - {req_data['role_title']}' (ID: {req_id}).")

    # 9. Live Deterministic Matching
    print("\n[9] Testing live deterministic candidate matching...")
    status, match_data, _ = request("POST", f"/api/v1/placements/requirements/{req_id}/match", token=coord_token)
    assert status == 200, f"Matching failed: {match_data}"
    assert "matches" in match_data
    assert match_data["total_candidates"] >= 2
    
    # Check John Doe
    john_match = next((m for m in match_data["matches"] if "John Doe" in m["full_name"]), None)
    assert john_match is not None, "John Doe not evaluated in matching!"
    assert john_match["is_matched"] is True, f"Expected John Doe to match: {john_match}"
    assert john_match["criteria_results"]["cgpa"]["passed"] is True
    assert john_match["criteria_results"]["branch"]["passed"] is True
    assert john_match["criteria_results"]["skills"]["Python"]["passed"] is True
    assert len(john_match["failure_reasons"]) == 0
    print(f"✓ Deterministic matching correctly evaluated John Doe as MATCHED based on real DB criteria.")

    # Verify no ranking or score attributes
    for m in match_data["matches"]:
        assert "rank" not in m
        assert "score" not in m
        assert "winner" not in m
        assert "best_candidate" not in m
    print("✓ Strict non-ranking rule validated: Zero score, ranking, or winner labels.")

    # 10. Live Assessment Request
    print("\n[10] Testing live coordinator assessment request...")
    status, as_req_res, _ = request("POST", "/api/v1/assessments/request", {
        "student_id": john_id,
        "skill_id": "Python",
        "type": "FOLLOW_UP"
    }, token=coord_token)
    assert status in (200, 201), f"Assessment request failed with {status}: {as_req_res}"
    print(f"✓ Assessment request executed: {as_req_res['message']}.")

    # 11. Live CSV Export & Security Verification
    print("\n[11] Testing live secure CSV export...")
    status, csv_data, headers = request("GET", f"/api/v1/placements/requirements/{req_id}/export", token=coord_token)
    assert status == 200, f"CSV export failed with {status}"
    assert "text/csv" in headers.get("Content-Type", "")
    assert "John Doe" in csv_data
    assert "MATCHED" in csv_data

    # Security check on CSV text
    forbidden = ["password", "hashed_password", "access_token", "jwt", "bearer", "/storage/uploads"]
    for f in forbidden:
        assert f not in csv_data.lower(), f"Security violation: Sensitive term '{f}' found in CSV export!"
    print("✓ Secure CSV export verified: Correct content-type, accurate candidate data, strictly zero sensitive tokens.")

    print("\n========================================================")
    print("ALL PHASE 6 LIVE WORKFLOW TESTS PASSED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    run_live_test()
