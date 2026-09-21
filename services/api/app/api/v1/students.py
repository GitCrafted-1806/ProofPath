from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_student, require_coordinator
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.audit_log import AuditLog
from app.schemas.student import (
    StudentProfileResponse,
    StudentSkillResponse,
    StudentProfileUpdateRequest,
    PublicStudentProfileResponse,
    StudentDirectoryItemResponse,
    StudentDirectoryListResponse,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfileResponse)
def get_student_self_profile(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Retrieve the authenticated student's academic profile and individual skill verification states."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    # Fetch skills and format response
    student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    skills_response = [
        StudentSkillResponse(
            skill_id=ss.skill_id,
            skill_name=ss.skill.name if ss.skill else "Unknown",
            verification_status=ss.verification_status,
            updated_at=ss.updated_at
        )
        for ss in student_skills
    ]

    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        full_name=profile.full_name,
        qualification=profile.qualification,
        college_name=profile.college_name,
        branch=profile.branch,
        academic_year=profile.academic_year,
        cgpa=profile.cgpa,
        public_profile_id=profile.public_profile_id,
        is_public=profile.is_public,
        skills=skills_response
    )


@router.patch("/me", response_model=StudentProfileResponse)
def update_student_self_profile(
    request: StudentProfileUpdateRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Update profile fields for the authenticated student and persist changes to database."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    updated_fields = []
    if request.full_name is not None:
        profile.full_name = request.full_name.strip()
        updated_fields.append("full_name")
    if request.qualification is not None:
        profile.qualification = request.qualification.strip()
        updated_fields.append("qualification")
    if request.college_name is not None:
        profile.college_name = request.college_name.strip()
        updated_fields.append("college_name")
    if request.branch is not None:
        profile.branch = request.branch.strip()
        updated_fields.append("branch")
    if request.academic_year is not None:
        profile.academic_year = request.academic_year
        updated_fields.append("academic_year")
    if request.cgpa is not None:
        profile.cgpa = round(float(request.cgpa), 2)
        updated_fields.append("cgpa")
    if request.is_public is not None:
        profile.is_public = request.is_public
        updated_fields.append("is_public")

    if updated_fields:
        audit = AuditLog(
            user_id=current_user.id,
            action="PROFILE_UPDATED",
            details=f"Updated profile fields: {', '.join(updated_fields)}"
        )
        db.add(audit)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    skills_response = [
        StudentSkillResponse(
            skill_id=ss.skill_id,
            skill_name=ss.skill.name if ss.skill else "Unknown",
            verification_status=ss.verification_status,
            updated_at=ss.updated_at
        )
        for ss in student_skills
    ]

    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        full_name=profile.full_name,
        qualification=profile.qualification,
        college_name=profile.college_name,
        branch=profile.branch,
        academic_year=profile.academic_year,
        cgpa=profile.cgpa,
        public_profile_id=profile.public_profile_id,
        is_public=profile.is_public,
        skills=skills_response
    )


@router.get("/public/{public_profile_id}", response_model=PublicStudentProfileResponse)
def get_public_student_profile(
    public_profile_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve public student verification profile for resume link sharing (no auth required)."""
    profile = db.query(StudentProfile).filter(StudentProfile.public_profile_id == public_profile_id).first()
    if not profile or not profile.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public student profile not found or set to private."
        )

    student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    skills_response = [
        StudentSkillResponse(
            skill_id=ss.skill_id,
            skill_name=ss.skill.name if ss.skill else "Unknown",
            verification_status=ss.verification_status,
            updated_at=ss.updated_at
        )
        for ss in student_skills
    ]

    return PublicStudentProfileResponse(
        id=profile.id,
        full_name=profile.full_name,
        qualification=profile.qualification,
        college_name=profile.college_name,
        branch=profile.branch,
        academic_year=profile.academic_year,
        cgpa=profile.cgpa,
        public_profile_id=profile.public_profile_id,
        is_public=profile.is_public,
        skills=skills_response
    )


@router.get("", response_model=StudentDirectoryListResponse)
def list_students_directory(
    search: Optional[str] = Query(None, max_length=100, description="Search by name, email, or college"),
    branch: Optional[str] = Query(None, max_length=80, description="Filter by branch"),
    min_cgpa: Optional[float] = Query(None, ge=0.0, le=10.0, description="Filter by minimum CGPA"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Placement Coordinator endpoint to search and browse the student directory.
    Supports multi-field keyword filtering, branch filtering, and min CGPA filtering.
    """
    query = db.query(StudentProfile).join(User, StudentProfile.user_id == User.id)

    if search:
        search_clean = search.strip()
        if search_clean:
            search_pattern = f"%{search_clean}%"
            query = query.filter(
                or_(
                    StudentProfile.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    StudentProfile.college_name.ilike(search_pattern),
                )
            )

    if branch:
        branch_clean = branch.strip()
        if branch_clean:
            query = query.filter(StudentProfile.branch.ilike(f"%{branch_clean}%"))

    if min_cgpa is not None:
        min_cgpa_clean = round(float(min_cgpa), 2)
        query = query.filter(StudentProfile.cgpa >= min_cgpa_clean)

    total = query.count()
    profiles = query.order_by(StudentProfile.full_name.asc()).offset(skip).limit(limit).all()

    items: List[StudentDirectoryItemResponse] = []
    for p in profiles:
        student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == p.id).all()
        skills_resp = [
            StudentSkillResponse(
                skill_id=ss.skill_id,
                skill_name=ss.skill.name if ss.skill else "Unknown",
                verification_status=ss.verification_status,
                updated_at=ss.updated_at
            )
            for ss in student_skills
        ]
        verified_count = sum(
            1 for ss in student_skills
            if ss.verification_status == SkillVerificationStatus.SKILL_VERIFIED
        )

        items.append(
            StudentDirectoryItemResponse(
                id=p.id,
                user_id=p.user_id,
                email=p.user.email if p.user else "",
                full_name=p.full_name,
                qualification=p.qualification,
                college_name=p.college_name,
                branch=p.branch,
                academic_year=p.academic_year,
                cgpa=p.cgpa,
                public_profile_id=p.public_profile_id,
                is_public=p.is_public,
                skills_count=len(skills_resp),
                verified_skills_count=verified_count,
                skills=skills_resp
            )
        )

    return StudentDirectoryListResponse(total=total, students=items)


@router.get("/{student_id}", response_model=StudentProfileResponse)
def get_student_by_id(
    student_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Placement Coordinator endpoint to retrieve full details of any student profile.
    Accepts either student_profile.id or user.id.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile with ID '{student_id}' not found."
        )

    student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    skills_response = [
        StudentSkillResponse(
            skill_id=ss.skill_id,
            skill_name=ss.skill.name if ss.skill else "Unknown",
            verification_status=ss.verification_status,
            updated_at=ss.updated_at
        )
        for ss in student_skills
    ]

    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email if profile.user else "",
        full_name=profile.full_name,
        qualification=profile.qualification,
        college_name=profile.college_name,
        branch=profile.branch,
        academic_year=profile.academic_year,
        cgpa=profile.cgpa,
        public_profile_id=profile.public_profile_id,
        is_public=profile.is_public,
        skills=skills_response
    )

