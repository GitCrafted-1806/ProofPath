from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill, MVP_SKILLS
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.audit_log import AuditLog
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new student or placement coordinator account."""
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Hash password with bcrypt
    hashed = get_password_hash(req.password)
    user = User(
        email=req.email,
        hashed_password=hashed,
        role=req.role
    )
    db.add(user)
    db.flush()

    # If student, initialize profile and default unverified skill records
    if req.role == UserRole.STUDENT:
        profile = StudentProfile(
            user_id=user.id,
            full_name=req.full_name or "New Student",
            qualification=req.qualification or "B.Tech",
            college_name=req.college_name or "College of Engineering",
            branch=req.branch or "CSE",
            academic_year=req.academic_year or 2026,
            cgpa=req.cgpa or 0.0,
            is_public=True
        )
        db.add(profile)
        db.flush()

        # Seed the 4 MVP skills into StudentSkill (initially UNVERIFIED)
        for skill_name in MVP_SKILLS:
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if skill:
                student_skill = StudentSkill(
                    student_id=profile.id,
                    skill_id=skill.id,
                    verification_status=SkillVerificationStatus.UNVERIFIED
                )
                db.add(student_skill)

    # Record audit log
    audit = AuditLog(
        user_id=user.id,
        action="REGISTER",
        details=f"User registered with role {req.role.value}"
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a JWT access token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    # Issue JWT
    token_payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(token_payload)

    # Record audit log
    audit = AuditLog(
        user_id=user.id,
        action="LOGIN",
        details="User successfully authenticated via email/password"
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        role=user.role,
        user_id=user.id,
        email=user.email
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the profile and role details of the authenticated user."""
    return current_user
