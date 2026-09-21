import io
import csv
import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_coordinator
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.placement_requirement import PlacementRequirement
from app.models.audit_log import AuditLog
from app.schemas.placement import (
    PlacementRequirementCreateRequest,
    PlacementRequirementResponse,
    CandidateMatchItem,
    PlacementMatchResponse,
)

router = APIRouter(prefix="/placements", tags=["Placements"])

STATUS_HIERARCHY = {
    "UNVERIFIED": 0,
    "EVIDENCE_SUPPORTED": 1,
    "SKILL_ASSESSED": 2,
    "SKILL_VERIFIED": 3,
}


def evaluate_student_match(
    profile: StudentProfile,
    email: str,
    requirement: PlacementRequirement,
    student_skills_map: Dict[str, str],
) -> CandidateMatchItem:
    """
    Deterministic matching logic for a candidate against a placement requirement.
    Binary evaluation per criterion without ranking, scores, or weighting.
    """
    # 1. CGPA Criterion
    cgpa_val = profile.cgpa or 0.0
    cgpa_passed = cgpa_val >= requirement.min_cgpa

    # 2. Branch Criterion
    eligible_branches = requirement.eligible_branches or []
    if eligible_branches:
        branch_passed = any(
            profile.branch.strip().upper() == eb.strip().upper()
            for eb in eligible_branches
        )
    else:
        branch_passed = True

    # 3. Required Skills Criteria
    req_skills = requirement.required_skills or {}
    skills_results: Dict[str, Dict[str, Any]] = {}
    skills_passed = True

    for skill_name, required_level in req_skills.items():
        actual_level = student_skills_map.get(skill_name, "UNVERIFIED")
        actual_rank = STATUS_HIERARCHY.get(actual_level, 0)
        req_rank = STATUS_HIERARCHY.get(required_level, 0)

        passed = actual_rank >= req_rank
        if not passed:
            skills_passed = False

        skills_results[skill_name] = {
            "required": required_level,
            "actual": actual_level,
            "passed": passed,
        }

    # Overall Binary Match
    is_matched = cgpa_passed and branch_passed and skills_passed

    # Failure Reasons compilation
    failure_reasons: List[str] = []
    if not cgpa_passed:
        failure_reasons.append(
            f"CGPA {cgpa_val:.2f} is below the minimum required {requirement.min_cgpa:.2f}"
        )
    if not branch_passed:
        branches_str = ", ".join(eligible_branches)
        failure_reasons.append(
            f"Branch '{profile.branch}' is not in eligible branches ({branches_str})"
        )
    for skill_name, res in skills_results.items():
        if not res["passed"]:
            failure_reasons.append(
                f"Skill '{skill_name}' is {res['actual']} (requires {res['required']})"
            )

    criteria_results = {
        "cgpa": {
            "required": requirement.min_cgpa,
            "actual": cgpa_val,
            "passed": cgpa_passed,
        },
        "branch": {
            "eligible": eligible_branches,
            "actual": profile.branch,
            "passed": branch_passed,
        },
        "skills": skills_results,
    }

    return CandidateMatchItem(
        student_id=profile.id,
        full_name=profile.full_name,
        email=email,
        college_name=profile.college_name,
        branch=profile.branch,
        academic_year=profile.academic_year,
        cgpa=cgpa_val,
        is_matched=is_matched,
        criteria_results=criteria_results,
        failure_reasons=failure_reasons,
        skills=student_skills_map,
    )


@router.post("/requirements", response_model=PlacementRequirementResponse, status_code=status.HTTP_201_CREATED)
def create_placement_requirement(
    payload: PlacementRequirementCreateRequest,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """Create a new placement requirement criteria for company recruitment."""
    # Normalize skills
    clean_skills = {}
    for skill, level in payload.required_skills.items():
        normalized_level = level.strip().upper()
        if normalized_level not in STATUS_HIERARCHY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification status '{level}' for skill '{skill}'. Allowed: {list(STATUS_HIERARCHY.keys())}",
            )
        clean_skills[skill.strip()] = normalized_level

    clean_branches = [b.strip() for b in payload.eligible_branches if b.strip()]

    req = PlacementRequirement(
        coordinator_id=current_user.id,
        company_name=payload.company_name.strip(),
        role_title=payload.role_title.strip(),
        min_cgpa=round(float(payload.min_cgpa), 2),
        eligible_branches=clean_branches,
        required_skills=clean_skills,
    )
    db.add(req)

    audit = AuditLog(
        user_id=current_user.id,
        action="PLACEMENT_REQUIREMENT_CREATED",
        details=f"Coordinator {current_user.email} created requirement '{req.company_name} - {req.role_title}' (min CGPA {req.min_cgpa})",
    )
    db.add(audit)
    db.commit()
    db.refresh(req)

    return req


@router.get("/requirements", response_model=List[PlacementRequirementResponse])
def list_placement_requirements(
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """List all active placement requirements created by coordinators."""
    return db.query(PlacementRequirement).order_by(PlacementRequirement.created_at.desc()).all()


@router.get("/requirements/{requirement_id}", response_model=PlacementRequirementResponse)
def get_placement_requirement_detail(
    requirement_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific placement requirement."""
    req = db.query(PlacementRequirement).filter(PlacementRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement requirement '{requirement_id}' not found.",
        )
    return req


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_placement_requirement(
    requirement_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """Delete a placement requirement."""
    req = db.query(PlacementRequirement).filter(PlacementRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement requirement '{requirement_id}' not found.",
        )

    db.delete(req)
    audit = AuditLog(
        user_id=current_user.id,
        action="PLACEMENT_REQUIREMENT_DELETED",
        details=f"Coordinator {current_user.email} deleted requirement '{req.company_name} - {req.role_title}'",
    )
    db.add(audit)
    db.commit()
    return None


@router.post("/requirements/{requirement_id}/match", response_model=PlacementMatchResponse)
def match_candidates_for_requirement(
    requirement_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Deterministically match candidates against the specified placement requirement.
    Matches are computed from actual student data and verification statuses in the DB.
    Strictly avoids scores, candidate rankings, or winner labels.
    """
    req = db.query(PlacementRequirement).filter(PlacementRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement requirement '{requirement_id}' not found.",
        )

    students = db.query(StudentProfile).join(User, StudentProfile.user_id == User.id).all()

    matches: List[CandidateMatchItem] = []
    matched_count = 0
    unmatched_count = 0

    for s in students:
        # Fetch student skills
        ss_records = db.query(StudentSkill).filter(StudentSkill.student_id == s.id).all()
        student_skills_map = {
            ss.skill.name: ss.verification_status.value
            for ss in ss_records
            if ss.skill
        }

        email = s.user.email if s.user else ""
        match_item = evaluate_student_match(s, email, req, student_skills_map)

        if match_item.is_matched:
            matched_count += 1
        else:
            unmatched_count += 1

        matches.append(match_item)

    # Sort alphabetically by full name (pure deterministic ordering, NOT ranking/scoring)
    matches.sort(key=lambda m: m.full_name.lower())

    return PlacementMatchResponse(
        requirement=PlacementRequirementResponse.model_validate(req),
        total_candidates=len(students),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        matches=matches,
    )


@router.get("/requirements/{requirement_id}/export")
def export_placement_results_csv(
    requirement_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
):
    """
    Secure CSV export of candidate matching results.
    SECURITY RULES:
    - Never exports passwords, hashes, JWTs, OAuth tokens, GitHub tokens.
    - Never exports private filesystem paths or file URLs.
    - Exports strictly placement-relevant candidate fields and criteria outcomes.
    """
    req = db.query(PlacementRequirement).filter(PlacementRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement requirement '{requirement_id}' not found.",
        )

    students = db.query(StudentProfile).join(User, StudentProfile.user_id == User.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Safe headers
    writer.writerow([
        "Student Name",
        "Email",
        "College",
        "Branch",
        "Academic Year",
        "CGPA",
        "Match Status",
        "CGPA Requirement Met",
        "Branch Requirement Met",
        "Skills Verification Breakdown",
        "Unmet Criteria / Failure Reasons",
    ])

    for s in sorted(students, key=lambda x: x.full_name.lower()):
        ss_records = db.query(StudentSkill).filter(StudentSkill.student_id == s.id).all()
        student_skills_map = {
            ss.skill.name: ss.verification_status.value
            for ss in ss_records
            if ss.skill
        }
        email = s.user.email if s.user else ""
        item = evaluate_student_match(s, email, req, student_skills_map)

        # Build skills breakdown text
        skills_breakdown_parts = []
        for s_name, res in item.criteria_results["skills"].items():
            status_text = "MET" if res["passed"] else "NOT_MET"
            skills_breakdown_parts.append(
                f"{s_name}: {res['actual']} (required: {res['required']}, {status_text})"
            )
        skills_str = "; ".join(skills_breakdown_parts) if skills_breakdown_parts else "N/A"

        unmet_str = "; ".join(item.failure_reasons) if item.failure_reasons else "None"

        writer.writerow([
            item.full_name,
            item.email,
            item.college_name or "N/A",
            item.branch,
            item.academic_year or "N/A",
            f"{item.cgpa:.2f}",
            "MATCHED" if item.is_matched else "NOT_MATCHED",
            "YES" if item.criteria_results["cgpa"]["passed"] else "NO",
            "YES" if item.criteria_results["branch"]["passed"] else "NO",
            skills_str,
            unmet_str,
        ])

    csv_content = output.getvalue()
    output.close()

    # Sanitize filename
    clean_company = re.sub(r'[^a-zA-Z0-9_\-]', '_', req.company_name.lower())
    clean_role = re.sub(r'[^a-zA-Z0-9_\-]', '_', req.role_title.lower())
    filename = f"{clean_company}_{clean_role}_candidates.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
