from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.student_skill import SkillVerificationStatus, StudentSkill
from app.models.skill import Skill
from app.models.evidence import Evidence, EvidenceType
from app.models.assessment import Assessment
from app.models.audit_log import AuditLog


def check_skill_prerequisites(
    student_id: str,
    skill_id: str,
    db: Session
) -> Tuple[bool, bool, bool, bool]:
    """
    Check the four independent verification criteria for a given student and skill:
    1. has_supporting_evidence (CERTIFICATE or PROJECT_DOCUMENT)
    2. passed_practical_assessment (PRACTICAL assessment with passed=True)
    3. has_project_evidence (GITHUB_REPO evidence mapped to this skill)
    4. passed_followup (FOLLOW_UP assessment with passed=True)

    Returns:
        Tuple of 4 booleans: (has_supporting, passed_assessment, has_project, passed_followup)
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return False, False, False, False

    skill_identifiers = {skill.id, skill.name}

    # 1. Supporting Evidence: CERTIFICATE or PROJECT_DOCUMENT
    all_evidence = db.query(Evidence).filter(Evidence.student_id == student_id).all()
    has_supporting_evidence = False
    has_project_evidence = False

    for ev in all_evidence:
        mapped = set(ev.mapped_skills or [])
        is_mapped_to_skill = bool(mapped.intersection(skill_identifiers))
        if is_mapped_to_skill:
            if ev.type in [EvidenceType.CERTIFICATE, EvidenceType.PROJECT_DOCUMENT]:
                has_supporting_evidence = True
            elif ev.type == EvidenceType.GITHUB_REPO:
                has_project_evidence = True

    # 2. Practical Assessment
    passed_assessment = db.query(Assessment).filter(
        Assessment.student_id == student_id,
        Assessment.skill_id == skill_id,
        Assessment.type == "PRACTICAL",
        Assessment.passed == True
    ).first() is not None

    # 3. Follow-up Assessment
    passed_followup = db.query(Assessment).filter(
        Assessment.student_id == student_id,
        Assessment.skill_id == skill_id,
        Assessment.type == "FOLLOW_UP",
        Assessment.passed == True
    ).first() is not None

    return (
        has_supporting_evidence,
        passed_assessment,
        has_project_evidence,
        passed_followup
    )


def compute_skill_status(
    student_id: str,
    skill_id: str,
    db: Session
) -> SkillVerificationStatus:
    """
    Pure deterministic business logic engine.
    AI is strictly NOT involved.

    Evaluation rules:
    - Missing supporting evidence -> UNVERIFIED
    - Supporting evidence only -> EVIDENCE_SUPPORTED
    - Supporting evidence + passed practical assessment -> SKILL_ASSESSED
    - Supporting evidence + passed practical assessment + GitHub project evidence + passed follow-up -> SKILL_VERIFIED

    Note: Any missing link prevents moving up to SKILL_VERIFIED.
    """
    (
        has_supporting_evidence,
        passed_assessment,
        has_project_evidence,
        passed_followup
    ) = check_skill_prerequisites(student_id, skill_id, db)

    # Rule 1: Without supporting evidence, the skill remains UNVERIFIED
    if not has_supporting_evidence:
        return SkillVerificationStatus.UNVERIFIED

    # Rule 2: Supporting evidence present, but practical assessment not passed
    if not passed_assessment:
        return SkillVerificationStatus.EVIDENCE_SUPPORTED

    # Rule 3: Supporting evidence + passed assessment, but incomplete project implementation or follow-up
    if passed_assessment and not (has_project_evidence and passed_followup):
        return SkillVerificationStatus.SKILL_ASSESSED

    # Rule 4: Supporting evidence + passed assessment + GitHub project evidence + passed follow-up
    if (
        has_supporting_evidence
        and has_project_evidence
        and passed_assessment
        and passed_followup
    ):
        return SkillVerificationStatus.SKILL_VERIFIED

    return SkillVerificationStatus.UNVERIFIED


def update_and_persist_skill_status(
    student_id: str,
    skill_id: str,
    db: Session
) -> Optional[StudentSkill]:
    """
    Compute deterministic status for student skill and persist changes to the database.
    Logs to AuditLog if the verification status changes.
    """
    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == student_id,
        StudentSkill.skill_id == skill_id
    ).first()

    if not student_skill:
        return None

    new_status = compute_skill_status(student_id, skill_id, db)
    old_status = student_skill.verification_status

    if old_status != new_status:
        student_skill.verification_status = new_status
        db.add(student_skill)

        # Audit log
        audit = AuditLog(
            user_id=student_id,
            action="VERIFICATION_STATUS_CHANGE",
            details=f"Skill ID {skill_id} transitioned from {old_status.value} to {new_status.value}"
        )
        db.add(audit)
        db.commit()
        db.refresh(student_skill)

    return student_skill
