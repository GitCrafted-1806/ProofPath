from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_student
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill
from app.schemas.student import StudentProfileResponse, StudentSkillResponse

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
