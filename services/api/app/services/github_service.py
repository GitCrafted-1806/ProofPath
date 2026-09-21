import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
import httpx
import jwt
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

# Deterministic mock repositories for DEMO_MODE
DEMO_GITHUB_REPOSITORIES: List[Dict[str, Any]] = [
    {
        "id": 101,
        "name": "analytics-pipeline",
        "full_name": "octocat-dev/analytics-pipeline",
        "owner": "octocat-dev",
        "description": "Production ETL pipeline built with Pandas and visualized with Matplotlib figures.",
        "html_url": "https://github.com/octocat-dev/analytics-pipeline",
        "default_branch": "main",
        "language": "Python",
        "stars": 14,
        "forks": 3,
        "is_private": False,
        "topics": ["python", "pandas", "data-analysis", "matplotlib"],
        "updated_at": "2025-05-10T12:00:00Z",
        "files": ["requirements.txt", "main.py", "README.md"],
        "dependencies": ["pandas>=2.0.0", "matplotlib>=3.7.0"],
        "readme_content": "# Analytics Pipeline\nAutomated ETL pipeline using pandas and matplotlib for visualization."
    },
    {
        "id": 102,
        "name": "student-portfolio",
        "full_name": "octocat-dev/student-portfolio",
        "owner": "octocat-dev",
        "description": "Personal programming portfolio demonstrating algorithm implementations in Python.",
        "html_url": "https://github.com/octocat-dev/student-portfolio",
        "default_branch": "main",
        "language": "Python",
        "stars": 5,
        "forks": 0,
        "is_private": False,
        "topics": ["python", "algorithms", "data-structures"],
        "updated_at": "2025-04-20T08:30:00Z",
        "files": ["solution.py", "README.md"],
        "dependencies": [],
        "readme_content": "# Student Portfolio\nClean Python implementations of sorting and graph algorithms."
    },
    {
        "id": 103,
        "name": "web-scraper",
        "full_name": "octocat-dev/web-scraper",
        "owner": "octocat-dev",
        "description": "Web scraping and data cleaning scripts utilizing pandas dataframes.",
        "html_url": "https://github.com/octocat-dev/web-scraper",
        "default_branch": "main",
        "language": "Python",
        "stars": 2,
        "forks": 1,
        "is_private": False,
        "topics": ["scraping", "pandas"],
        "updated_at": "2025-03-15T16:45:00Z",
        "files": ["scraper.py", "requirements.txt", "README.md"],
        "dependencies": ["pandas", "beautifulsoup4"],
        "readme_content": "# Web Scraper\nExtracts and parses data into structured pandas DataFrames."
    }
]


def create_oauth_state(student_id: str) -> str:
    """
    Generate a cryptographically signed state JWT for CSRF protection and callback authentication.
    Carries the student_id with a strict 10-minute validity.
    """
    payload = {
        "sub": student_id,
        "type": "github_oauth_state",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def validate_oauth_state(state: str) -> str:
    """
    Validate the signed OAuth state parameter from callback.
    Verifies signature, expiration, and type.
    Returns the student_id embedded in the state JWT.
    Raises HTTPException(400) on invalid or expired state.
    """
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state parameter."
        )

    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "github_oauth_state":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state type."
            )
        student_id = payload.get("sub")
        if not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State payload missing student identifier."
            )
        return student_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth state token has expired. Please initiate connection again."
        )
    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or tampered GitHub OAuth state parameter."
        )


async def exchange_code_for_token(code: str) -> Tuple[str, Dict[str, Any]]:
    """
    Exchange authorization code for an access token and fetch GitHub user profile.
    Supports DEMO_MODE with mock credentials, and live GitHub OAuth when DEMO_MODE=false.
    
    Returns:
        Tuple[encrypted_token, user_profile_dict]
    """
    # Demo Mode or mock code handler
    if settings.DEMO_MODE or code.startswith("demo_") or code.startswith("mock_"):
        mock_token = "mock_gho_octocat_demo_token_xyz"
        mock_user = {
            "id": 583231,
            "login": "octocat-dev",
            "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
            "html_url": "https://github.com/octocat-dev"
        }
        return encrypt_token(mock_token), mock_user

    # Live Mode: require explicit environment credentials
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth is not configured. Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET in environment."
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Exchange code for access token
        token_res = await client.post(
            settings.GITHUB_OAUTH_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"}
        )

        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub OAuth token exchange failed with HTTP {token_res.status_code}."
            )

        token_data = token_res.json()
        if "error" in token_data:
            error_msg = token_data.get("error_description") or token_data.get("error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub authorization failed: {error_msg}"
            )

        raw_access_token = token_data.get("access_token")
        if not raw_access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="GitHub response did not contain an access token."
            )

        # 2. Fetch authenticated user profile
        user_res = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/user",
            headers={
                "Authorization": f"Bearer {raw_access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve GitHub user profile from API."
            )

        user_profile = user_res.json()
        return encrypt_token(raw_access_token), user_profile


async def fetch_student_repositories(encrypted_token: Optional[str]) -> List[Dict[str, Any]]:
    """
    Fetch repositories for the connected GitHub account.
    Returns normalized list of repository dictionaries.
    """
    if settings.DEMO_MODE or not encrypted_token:
        return DEMO_GITHUB_REPOSITORIES

    plain_token = decrypt_token(encrypted_token)
    if not plain_token or plain_token.startswith("mock_"):
        return DEMO_GITHUB_REPOSITORIES

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/user/repos?sort=updated&per_page=30",
            headers={
                "Authorization": f"Bearer {plain_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        if res.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Stored GitHub access token has expired or was revoked. Please reconnect."
            )
        elif res.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub API rate limit exceeded or access forbidden."
            )
        elif res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch repositories from GitHub (HTTP {res.status_code})."
            )

        raw_repos = res.json()
        normalized_repos = []
        for r in raw_repos:
            normalized_repos.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "owner": r.get("owner", {}).get("login", ""),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "default_branch": r.get("default_branch", "main"),
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "is_private": r.get("private", False),
                "topics": r.get("topics", []),
                "updated_at": r.get("updated_at"),
            })

        return normalized_repos


async def fetch_repository_details(encrypted_token: Optional[str], repo_full_name: str) -> Dict[str, Any]:
    """
    Fetch comprehensive repository details, language breakdown, and dependencies for signal analysis.
    """
    # Demo Mode or mock account check
    if settings.DEMO_MODE or not encrypted_token:
        for r in DEMO_GITHUB_REPOSITORIES:
            if r["full_name"].lower() == repo_full_name.lower():
                return r
        # If not found in catalog, construct fallback mock
        owner, name = repo_full_name.split("/") if "/" in repo_full_name else ("octocat-dev", repo_full_name)
        return {
            "id": 999,
            "name": name,
            "full_name": repo_full_name,
            "owner": owner,
            "description": f"Repository {repo_full_name}",
            "html_url": f"https://github.com/{repo_full_name}",
            "default_branch": "main",
            "language": "Python",
            "stars": 0,
            "forks": 0,
            "is_private": False,
            "topics": ["python"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "files": ["main.py"],
            "dependencies": [],
            "readme_content": f"# {name}\nPython project repository."
        }

    plain_token = decrypt_token(encrypted_token)
    if not plain_token or plain_token.startswith("mock_"):
        for r in DEMO_GITHUB_REPOSITORIES:
            if r["full_name"].lower() == repo_full_name.lower():
                return r

    # Live Mode
    async with httpx.AsyncClient(timeout=15.0) as client:
        repo_res = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/repos/{repo_full_name}",
            headers={
                "Authorization": f"Bearer {plain_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        if repo_res.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GitHub repository '{repo_full_name}' not found."
            )
        elif repo_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to query repository '{repo_full_name}' from GitHub API."
            )

        r = repo_res.json()
        details = {
            "id": r.get("id"),
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "owner": r.get("owner", {}).get("login", ""),
            "description": r.get("description") or "",
            "html_url": r.get("html_url"),
            "default_branch": r.get("default_branch", "main"),
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "is_private": r.get("private", False),
            "topics": r.get("topics", []),
            "updated_at": r.get("updated_at"),
            "dependencies": [],
            "readme_content": ""
        }

        # Try to inspect requirements.txt if present
        try:
            req_res = await client.get(
                f"{settings.GITHUB_API_BASE_URL}/repos/{repo_full_name}/contents/requirements.txt",
                headers={
                    "Authorization": f"Bearer {plain_token}",
                    "Accept": "application/vnd.github.raw+json"
                }
            )
            if req_res.status_code == 200:
                details["dependencies"] = [line.strip() for line in req_res.text.splitlines() if line.strip()]
        except Exception:
            pass

        return details
