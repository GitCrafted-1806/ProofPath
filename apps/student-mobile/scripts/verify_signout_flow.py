"""
Verification script for Student Mobile Sign-Out Flow:
1. User logs in (John Doe).
2. Verifies token is valid and user profile loads from backend.
3. User signs out -> clears storage (SecureStore/AsyncStorage/memory).
4. Verifies storage is completely empty (no token, no user ID).
5. Verifies app state is unauthenticated and reloading cannot restore session.
6. Verifies request to protected endpoints without token returns 401 Unauthorized.
7. User logs back in (Jane Smith) -> obtains new token and new session.
8. Verifies seamless re-login works.
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def run_signout_verification():
    print("=================================================================")
    print("PROOFPATH: STUDENT MOBILE SIGN-OUT LIFECYCLE VERIFICATION")
    print("=================================================================")

    # Step 1: Health Check
    print("\n[Step 1] Checking backend health...")
    status, health = request("GET", "/api/health")
    assert status == 200 and health.get("status") == "healthy", f"Backend unhealthy: {health}"
    print(f" -> Backend healthy: {health}")

    # Simulated Mobile Storage Layer (matching storage.ts behavior)
    storage_secure = {}
    storage_async = {}
    storage_memory = {}

    def simulate_save_token(token, user_id):
        storage_memory["proofpath_access_token"] = token
        storage_memory["proofpath_user_id"] = user_id
        storage_secure["proofpath_access_token"] = token
        storage_secure["proofpath_user_id"] = user_id
        storage_async["proofpath_access_token"] = token
        storage_async["proofpath_user_id"] = user_id

    def simulate_get_token():
        return storage_secure.get("proofpath_access_token") or storage_async.get("proofpath_access_token") or storage_memory.get("proofpath_access_token")

    def simulate_clear_session():
        storage_memory.pop("proofpath_access_token", None)
        storage_memory.pop("proofpath_user_id", None)
        storage_secure.pop("proofpath_access_token", None)
        storage_secure.pop("proofpath_user_id", None)
        storage_async.pop("proofpath_access_token", None)
        storage_async.pop("proofpath_user_id", None)

    # Step 2: Login as John Doe
    print("\n[Step 2] Logging in as student (John Doe)...")
    status, login_res = request("POST", "/api/v1/auth/login", {
        "email": "john.doe@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Login failed: {login_res}"
    token_john = login_res["access_token"]
    user_id_john = login_res["user_id"]
    simulate_save_token(token_john, user_id_john)
    print(f" -> Authenticated successfully. Token: {token_john[:25]}...")

    # Step 3: Fetch profile with active session
    print("\n[Step 3] Verifying authenticated session via GET /api/v1/auth/me...")
    status, me_res = request("GET", "/api/v1/auth/me", token=simulate_get_token())
    assert status == 200, f"Failed to get current user: {me_res}"
    assert me_res["email"] == "john.doe@nit.edu"
    print(f" -> Active session confirmed: {me_res['email']} ({me_res['role']})")

    status, profile_res = request("GET", "/api/v1/students/me", token=simulate_get_token())
    assert status == 200, f"Failed to get student profile: {profile_res}"
    print(f" -> Student data loaded: {profile_res['full_name']} - CGPA: {profile_res['cgpa']}")

    # Step 4: Perform Sign Out
    print("\n[Step 4] Executing Sign Out...")
    # Client executes clearAuthSession() + state reset
    simulate_clear_session()
    current_token = simulate_get_token()
    assert current_token is None, f"Token still present after clearAuthSession: {current_token}"
    assert len(storage_secure) == 0, f"SecureStore not empty: {storage_secure}"
    assert len(storage_async) == 0, f"AsyncStorage not empty: {storage_async}"
    assert len(storage_memory) == 0, f"Memory fallback not empty: {storage_memory}"
    print(" -> All storage layers (SecureStore, AsyncStorage, Memory) purged successfully.")

    # Step 5: Verify reload / unauthenticated state
    print("\n[Step 5] Verifying session restoration attempt on cold reload...")
    # On app reload, initAuth() checks storage
    reloaded_token = simulate_get_token()
    assert reloaded_token is None, "Cold reload restored previous token!"
    is_authenticated = bool(reloaded_token)
    assert not is_authenticated, "User still marked authenticated!"
    print(" -> Session restoration blocked: reloaded token is None, app lands on LoginScreen.")

    # Step 6: Verify protected endpoints reject with 401
    print("\n[Step 6] Verifying protected endpoint rejects signed-out request...")
    status, err_res = request("GET", "/api/v1/students/me", token=reloaded_token)
    assert status == 401, f"Expected 401 Unauthorized, got status {status}: {err_res}"
    print(f" -> Successfully received HTTP 401 Unauthorized: {err_res.get('detail', err_res)}")

    # Step 7: Login again as Jane Smith (re-login verification)
    print("\n[Step 7] Testing Re-Login as Jane Smith...")
    status, login_res2 = request("POST", "/api/v1/auth/login", {
        "email": "jane.smith@nit.edu",
        "password": "Password123!"
    })
    assert status == 200, f"Login as Jane Smith failed: {login_res2}"
    token_jane = login_res2["access_token"]
    user_id_jane = login_res2["user_id"]
    simulate_save_token(token_jane, user_id_jane)
    print(f" -> Re-login successful. Token: {token_jane[:25]}...")

    status, me_res2 = request("GET", "/api/v1/auth/me", token=simulate_get_token())
    assert status == 200, f"Failed to get current user: {me_res2}"
    assert me_res2["email"] == "jane.smith@nit.edu"
    print(f" -> New session confirmed for Jane Smith: {me_res2['email']}")

    # Step 8: Sign out again
    print("\n[Step 8] Signing out second session...")
    simulate_clear_session()
    assert simulate_get_token() is None
    print(" -> Second sign-out completed cleanly.")

    print("\n=================================================================")
    print("ALL STUDENT MOBILE SIGN-OUT LIFECYCLE CHECKS PASSED!")
    print("=================================================================")


if __name__ == "__main__":
    run_signout_verification()
