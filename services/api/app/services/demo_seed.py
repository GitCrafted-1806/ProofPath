from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill, MVP_SKILLS
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.assessment import Assessment
from app.models.audit_log import AuditLog
from app.mock_data.fixtures import DEMO_COORDINATOR, DEMO_STUDENTS


def seed_mvp_skills(db: Session) -> dict:
    """Ensure the 4 MVP skills exist in database."""
    skill_map = {}
    skill_descriptions = {
        "Python": "Core Python programming, data structures, algorithms, and OOP principles.",
        "Pandas": "Data manipulation, DataFrame querying, cleaning, and time-series transformation.",
        "Matplotlib": "2D data visualization, statistical plots, custom figures, and subplots.",
        "Git/GitHub": "Distributed version control, branching strategies, PRs, and repository workflows."
    }

    for name in MVP_SKILLS:
        skill = db.query(Skill).filter(Skill.name == name).first()
        if not skill:
            skill = Skill(
                name=name,
                description=skill_descriptions.get(name, f"{name} skill proficiency")
            )
            db.add(skill)
            db.flush()
        skill_map[name] = skill

    db.commit()
    return skill_map


def seed_demo_data(db: Session, force_reset: bool = False) -> dict:
    """
    Seed initial realistic demo dataset:
    - 4 MVP Skills
    - Placement Coordinator
    - John Doe (B.Tech CSE, CGPA 8.2 with verified skill states)
    - 3 comparison students for criteria matching
    """
    if force_reset:
        # Clear existing data in reverse dependency order
        db.query(AuditLog).delete()
        db.query(Assessment).delete()
        db.query(Evidence).delete()
        db.query(StudentSkill).delete()
        db.query(StudentProfile).delete()
        db.query(User).delete()
        db.commit()

    # 1. Seed Skills
    skill_map = seed_mvp_skills(db)

    # 2. Seed Placement Coordinator
    coordinator = db.query(User).filter(User.email == DEMO_COORDINATOR["email"]).first()
    if not coordinator:
        coordinator = User(
            email=DEMO_COORDINATOR["email"],
            hashed_password=get_password_hash(DEMO_COORDINATOR["password"]),
            role=UserRole.PLACEMENT_COORDINATOR
        )
        db.add(coordinator)
        db.commit()
        db.refresh(coordinator)

    # 3. Seed Students
    seeded_students = []
    for s_data in DEMO_STUDENTS:
        user = db.query(User).filter(User.email == s_data["email"]).first()
        if not user:
            user = User(
                email=s_data["email"],
                hashed_password=get_password_hash(s_data["password"]),
                role=UserRole.STUDENT
            )
            db.add(user)
            db.flush()

            profile = StudentProfile(
                user_id=user.id,
                full_name=s_data["full_name"],
                qualification=s_data["qualification"],
                college_name=s_data["college_name"],
                branch=s_data["branch"],
                academic_year=s_data["academic_year"],
                cgpa=s_data["cgpa"],
                is_public=True
            )
            db.add(profile)
            db.flush()

            # Seed evidence & assessments according to target states
            for skill_name, state_str in s_data["skill_states"].items():
                skill = skill_map[skill_name]
                status_enum = SkillVerificationStatus(state_str)

                # Assign student skill record
                student_skill = StudentSkill(
                    student_id=profile.id,
                    skill_id=skill.id,
                    verification_status=status_enum
                )
                db.add(student_skill)

                # Seed supporting evidence if at least EVIDENCE_SUPPORTED
                if status_enum in [
                    SkillVerificationStatus.EVIDENCE_SUPPORTED,
                    SkillVerificationStatus.SKILL_ASSESSED,
                    SkillVerificationStatus.SKILL_VERIFIED
                ]:
                    cert_evidence = Evidence(
                        student_id=profile.id,
                        type=EvidenceType.CERTIFICATE,
                        original_filename=f"{skill_name.lower()}_certificate.pdf",
                        file_path=f"/evidence/{user.id}/{skill_name.lower()}_cert.pdf",
                        authenticity_state=AuthenticityState.SOURCE_SUPPORTED,
                        extracted_metadata={"issuer": "National Technical Board", "year": 2025},
                        mapped_skills=[skill_name]
                    )
                    db.add(cert_evidence)

                # Seed practical assessment if at least SKILL_ASSESSED
                if status_enum in [
                    SkillVerificationStatus.SKILL_ASSESSED,
                    SkillVerificationStatus.SKILL_VERIFIED
                ]:
                    prac_assessment = Assessment(
                        student_id=profile.id,
                        skill_id=skill.id,
                        type="PRACTICAL",
                        status="COMPLETED",
                        score=86.5,
                        passed=True,
                        evaluation_summary=f"Passed randomized practical assessment for {skill_name} with 86.5% accuracy.",
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(prac_assessment)

                # Seed GitHub project evidence & follow-up check if SKILL_VERIFIED
                if status_enum == SkillVerificationStatus.SKILL_VERIFIED:
                    proj_name = s_data.get("project_name") or "Analytical Engine"
                    github_evidence = Evidence(
                        student_id=profile.id,
                        type=EvidenceType.GITHUB_REPO,
                        original_filename=None,
                        file_path=f"https://github.com/student/{proj_name.lower().replace(' ', '-')}",
                        authenticity_state=AuthenticityState.SOURCE_SUPPORTED,
                        extracted_metadata={
                            "repo_name": proj_name,
                            "languages": ["Python"],
                            "description": "Production analysis script demonstrating algorithms and clean logic."
                        },
                        mapped_skills=[skill_name]
                    )
                    db.add(github_evidence)

                    follow_up = Assessment(
                        student_id=profile.id,
                        skill_id=skill.id,
                        type="FOLLOW_UP",
                        status="COMPLETED",
                        score=91.0,
                        passed=True,
                        evaluation_summary="Passed code explanation and deep architectural follow-up check.",
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(follow_up)

            db.commit()
            seeded_students.append(s_data["full_name"])

    # Audit log entry for DEMO initialization
    audit = AuditLog(
        user_id=coordinator.id if coordinator else None,
        action="DEMO_RESET",
        details="Demo dataset successfully initialized with 4 MVP skills, 1 coordinator, and 4 students."
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "coordinator_email": DEMO_COORDINATOR["email"],
        "seeded_students": seeded_students,
        "mvp_skills": list(skill_map.keys())
    }
