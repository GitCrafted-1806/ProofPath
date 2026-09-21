from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student, require_coordinator
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.github_account import GitHubAccount
from app.schemas.common import MessageResponse
from app.schemas.evidence import EvidenceResponse
from app.schemas.github import (
    GitHubConnectionStatusResponse,
    GitHubOAuthStartResponse,
    GitHubRepositoryResponse,
    GitHubRepoSelectRequest,
)
from app.services.github_service import (
    create_oauth_state,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_student_repositories,
    fetch_repository_details,
)
from app.services.github_analyzer import analyze_repository_evidence
from app.services.verification_engine import update_and_persist_skill_status

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/status", response_model=GitHubConnectionStatusResponse)
def get_github_connection_status(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Retrieve GitHub connection status for the authenticated student (never leaks access token)."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    account = db.query(GitHubAccount).filter(GitHubAccount.student_id == profile.id).first()
    if not account:
        return GitHubConnectionStatusResponse(is_connected=False)

    return GitHubConnectionStatusResponse(
        is_connected=True,
        github_username=account.github_username,
        avatar_url=account.avatar_url,
        profile_url=account.profile_url,
        connected_at=account.connected_at
    )


@router.get("/oauth/start", response_model=GitHubOAuthStartResponse)
def start_github_oauth(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Generate signed OAuth state JWT and return the authorization URL.
    In DEMO_MODE, returns a simulated callback URL with mock code.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    state = create_oauth_state(profile.id)

    if settings.DEMO_MODE:
        # In demo mode, authorize URL directly targets the local callback with mock code
        authorize_url = f"{settings.GITHUB_REDIRECT_URI}?code=demo_oauth_code_123&state={state}"
    else:
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth is not configured. Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET."
            )
        authorize_url = (
            f"{settings.GITHUB_OAUTH_AUTHORIZE_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
            f"&scope=read:user,repo"
            f"&state={state}"
        )

    return GitHubOAuthStartResponse(
        authorize_url=authorize_url,
        state=state,
        demo_mode=settings.DEMO_MODE
    )


@router.get("/callback", response_model=GitHubConnectionStatusResponse)
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub or mock flow"),
    state: str = Query(..., description="Signed state JWT parameter for callback auth and CSRF"),
    db: Session = Depends(get_db)
):
    """
    OAuth Callback: Does NOT require Bearer token authentication.
    Validates signed state JWT, extracts student_id, exchanges code for access token,
    and links the GitHub account to the student profile.
    """
    # 1. Authenticate and validate student identity via signed state JWT
    student_id = validate_oauth_state(state)

    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile associated with OAuth state not found."
        )

    # 2. Exchange code for access token and retrieve GitHub profile
    encrypted_token, user_profile = await exchange_code_for_token(code)

    github_user_id = str(user_profile.get("id"))
    github_username = user_profile.get("login") or "github-user"
    avatar_url = user_profile.get("avatar_url")
    profile_url = user_profile.get("html_url") or f"https://github.com/{github_username}"

    # 3. Upsert GitHubAccount record
    account = db.query(GitHubAccount).filter(GitHubAccount.student_id == profile.id).first()
    if not account:
        account = GitHubAccount(
            student_id=profile.id,
            github_user_id=github_user_id,
            github_username=github_username,
            avatar_url=avatar_url,
            profile_url=profile_url,
            encrypted_access_token=encrypted_token,
            scopes="read:user,repo"
        )
        db.add(account)
    else:
        account.github_user_id = github_user_id
        account.github_username = github_username
        account.avatar_url = avatar_url
        account.profile_url = profile_url
        account.encrypted_access_token = encrypted_token

    db.commit()
    db.refresh(account)

    return GitHubConnectionStatusResponse(
        is_connected=True,
        github_username=account.github_username,
        avatar_url=account.avatar_url,
        profile_url=account.profile_url,
        connected_at=account.connected_at
    )


@router.get("/repositories", response_model=List[GitHubRepositoryResponse])
async def list_github_repositories(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """List repositories from the student's connected GitHub account."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    account = db.query(GitHubAccount).filter(GitHubAccount.student_id == profile.id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account is not connected. Please connect your GitHub account first."
        )

    repos = await fetch_student_repositories(account.encrypted_access_token)
    return [GitHubRepositoryResponse(**r) for r in repos]


@router.post("/repositories/select", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def select_repository_evidence(
    payload: GitHubRepoSelectRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Select a GitHub repository as project evidence:
    - Analyzes deterministic signals (language, topics, dependencies, README)
    - Maps to MVP skills (Python, Pandas, Matplotlib, Git/GitHub)
    - Stores as Evidence record with type GITHUB_REPO (authenticity_state=SUBMITTED)
    - Invokes verification engine for mapped skills
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    account = db.query(GitHubAccount).filter(GitHubAccount.student_id == profile.id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account is not connected. Please connect your GitHub account first."
        )

    # 1. Fetch repository details
    repo_details = await fetch_repository_details(account.encrypted_access_token, payload.repo_full_name)

    # 2. Analyze signals and map MVP skills
    mapped_skills, metadata = analyze_repository_evidence(repo_details)

    html_url = repo_details.get("html_url") or f"https://github.com/{payload.repo_full_name}"
    repo_name = repo_details.get("name") or payload.repo_full_name.split("/")[-1]

    # 3. Create or update Evidence record
    evidence = db.query(Evidence).filter(
        Evidence.student_id == profile.id,
        Evidence.type == EvidenceType.GITHUB_REPO,
        Evidence.file_path == html_url
    ).first()

    if not evidence:
        evidence = Evidence(
            student_id=profile.id,
            type=EvidenceType.GITHUB_REPO,
            file_path=html_url,
            original_filename=repo_name,
            authenticity_state=AuthenticityState.SUBMITTED,
            extracted_metadata=metadata,
            mapped_skills=mapped_skills
        )
        db.add(evidence)
    else:
        evidence.original_filename = repo_name
        evidence.extracted_metadata = metadata
        evidence.mapped_skills = mapped_skills

    db.commit()
    db.refresh(evidence)

    # 4. Integrate with deterministic verification engine:
    # Ensure StudentSkill exists for each mapped skill and update status
    for skill_name in mapped_skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            student_skill = db.query(StudentSkill).filter(
                StudentSkill.student_id == profile.id,
                StudentSkill.skill_id == skill.id
            ).first()
            if not student_skill:
                student_skill = StudentSkill(
                    student_id=profile.id,
                    skill_id=skill.id,
                    verification_status=SkillVerificationStatus.UNVERIFIED
                )
                db.add(student_skill)
                db.commit()

            update_and_persist_skill_status(profile.id, skill.id, db)

    return evidence


@router.get("/evidence", response_model=List[EvidenceResponse])
def get_github_evidence(
    student_id: Optional[str] = Query(None, description="Optional filter for coordinator to view specific student"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve GitHub project evidence records for authenticated student or placement coordinator."""
    query = db.query(Evidence).filter(Evidence.type == EvidenceType.GITHUB_REPO)

    if current_user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found."
            )
        query = query.filter(Evidence.student_id == profile.id)
    elif current_user.role == UserRole.PLACEMENT_COORDINATOR:
        if student_id:
            query = query.filter(Evidence.student_id == student_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    evidences = query.order_by(Evidence.created_at.desc()).all()
    return evidences


@router.post("/disconnect", response_model=MessageResponse)
def disconnect_github(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Disconnect GitHub account from student profile and remove stored token."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    account = db.query(GitHubAccount).filter(GitHubAccount.student_id == profile.id).first()
    if account:
        db.delete(account)
        db.commit()

    return MessageResponse(message="GitHub account successfully disconnected.")
