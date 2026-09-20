from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.services.demo_seed import seed_demo_data
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


def check_demo_mode():
    """Verify DEMO_MODE is enabled."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode is disabled in this environment."
        )


@router.post("/reset")
def reset_demo_database(db: Session = Depends(get_db)):
    """Reset and re-seed the demo database with John Doe and baseline candidates."""
    check_demo_mode()
    result = seed_demo_data(db, force_reset=True)
    return {
        "message": "Demo database successfully reset and seeded.",
        "result": result
    }


@router.get("/status")
def get_demo_status(db: Session = Depends(get_db)):
    """Retrieve the current demo state, active demo accounts, and MVP skills."""
    check_demo_mode()
    students = db.query(StudentProfile).all()
    skills = db.query(Skill).all()
    coordinator = db.query(User).filter(User.role == UserRole.PLACEMENT_COORDINATOR).first()

    student_summaries = []
    for s in students:
        skill_states = {
            ss.skill.name: ss.verification_status.value
            for ss in s.skills if ss.skill
        }
        student_summaries.append({
            "name": s.full_name,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "skills": skill_states
        })

    return {
        "demo_mode": settings.DEMO_MODE,
        "database": settings.DATABASE_URL.split("///")[-1] if "///" in settings.DATABASE_URL else "configured",
        "mvp_skills": [sk.name for sk in skills],
        "coordinator_account": coordinator.email if coordinator else None,
        "total_students": len(students),
        "students": student_summaries
    }
