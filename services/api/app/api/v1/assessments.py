"""Skill assessment API endpoints for ProofPath Phase 4."""
from datetime import datetime, timezone
from typing import List, Union, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student, require_coordinator
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.assessment import Assessment
from app.models.audit_log import AuditLog
from app.schemas.assessment import (
    AssessmentStartRequest,
    AssessmentTakeResponse,
    AssessmentSubmitRequest,
    QuestionResultFeedback,
    AssessmentResultResponse,
    SkillAssessmentAvailabilityResponse,
    AssessmentHistoryItemResponse,
)
from app.schemas.placement import (
    AssessmentRequestCoordinatorPayload,
    AssessmentRequestCoordinatorResponse,
)
from app.services.assessment_service import (
    get_assessment_questions,
    mask_questions_for_client,
    evaluate_assessment_submission,
)
from app.services.verification_engine import (
    check_skill_prerequisites,
    update_and_persist_skill_status,
)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/available", response_model=List[SkillAssessmentAvailabilityResponse])
def get_available_assessments(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Check assessment availability for each of the student's skills based on deterministic prerequisites.
    - Practical requires supporting evidence (certificate or project document).
    - Follow-up requires passed practical assessment + GitHub project evidence.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    # Fetch all registered skills or MVP skills
    student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    results: List[SkillAssessmentAvailabilityResponse] = []

    for ss in student_skills:
        skill_name = ss.skill.name if ss.skill else "Unknown"
        has_supporting, passed_assessment, has_project, passed_followup = check_skill_prerequisites(
            profile.id, ss.skill_id, db
        )

        pending = db.query(Assessment).filter(
            Assessment.student_id == profile.id,
            Assessment.skill_id == ss.skill_id,
            Assessment.status == "PENDING",
        ).first()

        practical_available = has_supporting and not passed_assessment
        followup_available = passed_assessment and has_project and not passed_followup

        if not has_supporting:
            reason = "Requires supporting certificate or project document evidence before practical assessment."
        elif not passed_assessment:
            reason = "Ready for practical assessment."
        elif not has_project:
            reason = "Practical passed. Requires connected GitHub project evidence mapped to this skill before follow-up."
        elif not passed_followup:
            reason = "Ready for follow-up assessment."
        else:
            reason = "All assessments passed and skill verified."

        results.append(
            SkillAssessmentAvailabilityResponse(
                skill_id=ss.skill_id,
                skill_name=skill_name,
                current_status=ss.verification_status,
                practical_available=practical_available,
                followup_available=followup_available,
                pending_assessment_id=pending.id if pending else None,
                reason=reason,
            )
        )

    return results


@router.post("/start", response_model=AssessmentTakeResponse, status_code=status.HTTP_201_CREATED)
def start_assessment(
    request: AssessmentStartRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Initiate a PRACTICAL or FOLLOW_UP assessment for a skill.
    Strictly verifies deterministic prerequisites before issuing questions.
    SECURITY: Strips correct_answer and explanation from response payload.
    """
    req_type = request.type.strip().upper()
    if req_type not in ("PRACTICAL", "FOLLOW_UP"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assessment type '{request.type}'. Must be 'PRACTICAL' or 'FOLLOW_UP'.",
        )

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    skill = db.query(Skill).filter(Skill.id == request.skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID '{request.skill_id}' not found.",
        )

    # Ensure StudentSkill record exists
    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == profile.id,
        StudentSkill.skill_id == skill.id,
    ).first()
    if not student_skill:
        student_skill = StudentSkill(
            student_id=profile.id,
            skill_id=skill.id,
            verification_status=SkillVerificationStatus.UNVERIFIED,
        )
        db.add(student_skill)
        db.commit()

    # If there is already an active PENDING assessment for this student/skill/type, return it
    existing_pending = db.query(Assessment).filter(
        Assessment.student_id == profile.id,
        Assessment.skill_id == skill.id,
        Assessment.type == req_type,
        Assessment.status == "PENDING",
    ).first()
    if existing_pending:
        return AssessmentTakeResponse(
            id=existing_pending.id,
            student_id=existing_pending.student_id,
            skill_id=existing_pending.skill_id,
            skill_name=skill.name,
            type=existing_pending.type,
            status=existing_pending.status,
            questions=mask_questions_for_client(existing_pending.questions),
            created_at=existing_pending.created_at,
        )

    # Validate deterministic prerequisites
    has_supporting, passed_assessment, has_project, passed_followup = check_skill_prerequisites(
        profile.id, skill.id, db
    )

    if req_type == "PRACTICAL":
        if not has_supporting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supporting certificate or project document evidence is required before taking a practical assessment.",
            )
        if passed_assessment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practical assessment has already been completed and passed for this skill.",
            )
    elif req_type == "FOLLOW_UP":
        if not passed_assessment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practical assessment must be completed and passed before taking a follow-up assessment.",
            )
        if not has_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository evidence mapped to this skill is required before taking a follow-up assessment.",
            )
        if passed_followup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Follow-up assessment has already been completed and passed for this skill.",
            )

    # Load questions from curated fixtures
    try:
        raw_questions = get_assessment_questions(skill.name, req_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create Assessment entity
    assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type=req_type,
        status="PENDING",
        questions=raw_questions,
        score=None,
        passed=False,
        submission=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assessment)

    # Log audit event
    audit = AuditLog(
        user_id=current_user.id,
        action="ASSESSMENT_STARTED",
        details=f"Started {req_type} assessment for skill '{skill.name}'",
    )
    db.add(audit)
    db.commit()
    db.refresh(assessment)

    return AssessmentTakeResponse(
        id=assessment.id,
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        skill_name=skill.name,
        type=assessment.type,
        status=assessment.status,
        questions=mask_questions_for_client(assessment.questions),
        created_at=assessment.created_at,
    )


@router.post("/{assessment_id}/submit", response_model=AssessmentResultResponse)
def submit_assessment(
    assessment_id: str,
    request: AssessmentSubmitRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Submit answers for a pending assessment.
    Deterministically evaluates answers against stored rubric (passing threshold: 70.0%).
    Updates student skill verification status via the deterministic verification engine.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    # Strict ownership isolation: student can only submit their own assessment
    if assessment.student_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit this assessment.",
        )

    if assessment.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This assessment has already been submitted (status: {assessment.status}).",
        )

    # Deterministic scoring
    score, passed, feedback_raw, summary = evaluate_assessment_submission(
        assessment.questions,
        request.answers,
    )

    assessment.score = score
    assessment.passed = passed
    assessment.status = "COMPLETED" if passed else "FAILED"
    assessment.submission = request.answers
    assessment.evaluation_summary = summary
    assessment.completed_at = datetime.now(timezone.utc)
    db.add(assessment)
    db.flush()

    # Deterministic verification engine update
    updated_student_skill = update_and_persist_skill_status(profile.id, assessment.skill_id, db)
    new_status = (
        updated_student_skill.verification_status
        if updated_student_skill
        else SkillVerificationStatus.UNVERIFIED
    )

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="ASSESSMENT_SUBMITTED",
        details=f"Submitted {assessment.type} assessment for '{assessment.skill.name}': score={score}%, passed={passed}, new_status={new_status.value}",
    )
    db.add(audit)
    db.commit()
    db.refresh(assessment)

    return AssessmentResultResponse(
        id=assessment.id,
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        skill_name=assessment.skill.name,
        type=assessment.type,
        status=assessment.status,
        score=assessment.score,
        passed=assessment.passed,
        evaluation_summary=summary,
        completed_at=assessment.completed_at,
        feedback=[QuestionResultFeedback(**f) for f in feedback_raw],
        new_skill_status=new_status,
    )


@router.get("/history", response_model=List[AssessmentHistoryItemResponse])
def get_assessment_history(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Retrieve history of all assessments taken by the authenticated student."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    assessments = (
        db.query(Assessment)
        .filter(Assessment.student_id == profile.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    return [
        AssessmentHistoryItemResponse(
            id=a.id,
            skill_id=a.skill_id,
            skill_name=a.skill.name if a.skill else "Unknown",
            type=a.type,
            status=a.status,
            score=a.score,
            passed=a.passed,
            evaluation_summary=a.evaluation_summary,
            created_at=a.created_at,
            completed_at=a.completed_at,
        )
        for a in assessments
    ]


@router.get("/student/{student_id}", response_model=List[AssessmentHistoryItemResponse])
def get_student_assessment_history_for_coordinator(
    student_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Placement Coordinator audit endpoint to inspect assessment history for any student.
    Accepts either student profile ID or user ID.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile for ID '{student_id}' not found.",
        )

    assessments = (
        db.query(Assessment)
        .filter(Assessment.student_id == profile.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    return [
        AssessmentHistoryItemResponse(
            id=a.id,
            skill_id=a.skill_id,
            skill_name=a.skill.name if a.skill else "Unknown",
            type=a.type,
            status=a.status,
            score=a.score,
            passed=a.passed,
            evaluation_summary=a.evaluation_summary,
            created_at=a.created_at,
            completed_at=a.completed_at,
        )
        for a in assessments
    ]


@router.get("/{assessment_id}", response_model=Union[AssessmentTakeResponse, AssessmentResultResponse])
def get_assessment_details(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve assessment details.
    - If status is PENDING: returns masked questions without revealing answers.
    - If status is COMPLETED/FAILED: returns complete score, feedback, and skill status.
    - Permissions: students can only access their own assessments; placement coordinators can inspect any.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    # Check authorization
    if current_user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile or assessment.student_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this assessment.",
            )

    # If pending, return take response with masked answers
    if assessment.status == "PENDING":
        return AssessmentTakeResponse(
            id=assessment.id,
            student_id=assessment.student_id,
            skill_id=assessment.skill_id,
            skill_name=assessment.skill.name,
            type=assessment.type,
            status=assessment.status,
            questions=mask_questions_for_client(assessment.questions),
            created_at=assessment.created_at,
        )

    # If completed/failed, return detailed result
    score, passed, feedback_raw, summary = evaluate_assessment_submission(
        assessment.questions,
        assessment.submission or {},
    )

    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == assessment.student_id,
        StudentSkill.skill_id == assessment.skill_id,
    ).first()
    current_status = student_skill.verification_status if student_skill else SkillVerificationStatus.UNVERIFIED

    return AssessmentResultResponse(
        id=assessment.id,
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        skill_name=assessment.skill.name,
        type=assessment.type,
        status=assessment.status,
        score=assessment.score or 0.0,
        passed=assessment.passed,
        evaluation_summary=assessment.evaluation_summary or summary,
        completed_at=assessment.completed_at or assessment.created_at,
        feedback=[QuestionResultFeedback(**f) for f in feedback_raw],
        new_skill_status=current_status,
    )


@router.post("/request", response_model=AssessmentRequestCoordinatorResponse, status_code=status.HTTP_201_CREATED)
def request_assessment_by_coordinator(
    payload: AssessmentRequestCoordinatorPayload,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Placement Coordinator endpoint to explicitly request/assign an assessment for a student.
    Enables coordinators to test candidate readiness.
    Creates a PENDING assessment and generates an audit log.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == payload.student_id).first()
    if not profile:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == payload.student_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile for ID '{payload.student_id}' not found.",
        )

    skill = db.query(Skill).filter(Skill.id == payload.skill_id).first()
    if not skill:
        skill = db.query(Skill).filter(Skill.name.ilike(payload.skill_id)).first()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID or name '{payload.skill_id}' not found.",
        )

    req_type = payload.type.strip().upper()
    if req_type not in ("PRACTICAL", "FOLLOW_UP"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assessment type '{payload.type}'. Must be 'PRACTICAL' or 'FOLLOW_UP'.",
        )

    # Ensure StudentSkill record exists
    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == profile.id,
        StudentSkill.skill_id == skill.id,
    ).first()
    if not student_skill:
        student_skill = StudentSkill(
            student_id=profile.id,
            skill_id=skill.id,
            verification_status=SkillVerificationStatus.UNVERIFIED,
        )
        db.add(student_skill)
        db.commit()

    # Check for existing pending assessment
    existing_pending = db.query(Assessment).filter(
        Assessment.student_id == profile.id,
        Assessment.skill_id == skill.id,
        Assessment.type == req_type,
        Assessment.status == "PENDING",
    ).first()
    if existing_pending:
        return AssessmentRequestCoordinatorResponse(
            status="ALREADY_PENDING",
            message=f"A {req_type} assessment is already pending for student {profile.full_name}.",
            assessment_id=existing_pending.id,
            student_id=profile.id,
            skill_id=skill.id,
            type=req_type,
        )

    # Check if already passed
    already_passed = db.query(Assessment).filter(
        Assessment.student_id == profile.id,
        Assessment.skill_id == skill.id,
        Assessment.type == req_type,
        Assessment.passed == True,
    ).first()
    if already_passed:
        return AssessmentRequestCoordinatorResponse(
            status="ALREADY_PASSED",
            message=f"Student {profile.full_name} has already passed the {req_type} assessment for {skill.name}.",
            assessment_id=already_passed.id,
            student_id=profile.id,
            skill_id=skill.id,
            type=req_type,
        )

    # Load questions
    raw_questions = get_assessment_questions(skill.name, req_type)

    assessment = Assessment(
        student_id=profile.id,
        skill_id=skill.id,
        type=req_type,
        status="PENDING",
        questions=raw_questions,
    )
    db.add(assessment)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="ASSESSMENT_REQUESTED_BY_COORDINATOR",
        details=f"Coordinator {current_user.email} requested {req_type} assessment on {skill.name} for student {profile.full_name} ({profile.id})"
    )
    db.add(audit)
    db.commit()
    db.refresh(assessment)

    return AssessmentRequestCoordinatorResponse(
        status="SUCCESS",
        message=f"{req_type} assessment on {skill.name} successfully requested for {profile.full_name}.",
        assessment_id=assessment.id,
        student_id=profile.id,
        skill_id=skill.id,
        type=req_type,
    )
