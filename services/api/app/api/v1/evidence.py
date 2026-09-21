from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student, require_coordinator
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, SkillVerificationStatus
from app.models.evidence import Evidence, EvidenceType, AuthenticityState
from app.models.audit_log import AuditLog
from app.schemas.common import MessageResponse
from app.schemas.evidence import (
    EvidenceUploadType,
    EvidenceMetadataSchema,
    EvidenceResponse,
    EvidenceDetailResponse,
    EvidenceVerifyRequest,
)
from app.services.file_storage import save_upload_file, delete_file
from app.services.document_parser import parse_document
from app.services.skill_mapper import map_skills_from_text
from app.services.metadata_extractor import extract_document_metadata
from app.services.verification_engine import update_and_persist_skill_status

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    type: str = Form(default="CERTIFICATE"),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Upload an evidence file (CERTIFICATE or PROJECT_DOCUMENT, max 5 MB).
    Performs streaming validation, local document parsing, regex skill mapping,
    and stores evidence with default status SUBMITTED.
    """
    # 1. Restrict allowed upload evidence types in Phase 2
    try:
        validated_type = EvidenceUploadType(type.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid evidence type '{type}'. For file uploads, allowed types are: {[t.value for t in EvidenceUploadType]}. Note that GITHUB_REPO uploads are not permitted."
        )

    # 2. Get student profile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for authenticated user."
        )

    # 3. Stream and securely store file to private local disk
    storage_path, original_filename, file_size, sha256_hash, mime_type = await save_upload_file(
        file, profile.id
    )

    # 4. Parse document text via PyMuPDF / local OCR
    normalized_text, extraction_method = parse_document(storage_path, mime_type)

    # 5. Deterministic skill mapping to MVP skills
    mapped_skills = map_skills_from_text(normalized_text)

    # 6. Extract structured metadata (for tagging only - does NOT alter authenticity state)
    raw_metadata = extract_document_metadata(normalized_text, student_full_name=profile.full_name)
    raw_metadata.update({
        "file_size": file_size,
        "mime_type": mime_type,
        "sha256": sha256_hash,
        "extraction_method": extraction_method,
    })

    validated_metadata = EvidenceMetadataSchema(**raw_metadata).model_dump()

    # 7. Create evidence database record with default SUBMITTED state
    evidence = Evidence(
        student_id=profile.id,
        type=EvidenceType(validated_type.value),
        file_path=storage_path,
        original_filename=original_filename,
        authenticity_state=AuthenticityState.SUBMITTED,
        extracted_metadata=validated_metadata,
        mapped_skills=mapped_skills
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    # 8. Deterministic verification engine integration:
    # Ensure StudentSkill records exist and update their verification statuses
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


@router.get("/me", response_model=List[EvidenceResponse])
def get_my_evidence(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Retrieve all evidence submitted by the currently authenticated student."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    evidences = db.query(Evidence).filter(
        Evidence.student_id == profile.id
    ).order_by(Evidence.created_at.desc()).all()

    return evidences


@router.get("/student/{student_id}", response_model=List[EvidenceResponse])
def get_student_evidence(
    student_id: str,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Placement Coordinator endpoint to retrieve all evidence submitted by any student.
    Accepts student profile id or user id.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile with ID '{student_id}' not found."
        )

    evidences = db.query(Evidence).filter(
        Evidence.student_id == profile.id
    ).order_by(Evidence.created_at.desc()).all()

    return evidences


@router.get("/{evidence_id}", response_model=EvidenceDetailResponse)
def get_evidence_by_id(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve evidence details by ID with ownership/coordinator authorization."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found."
        )

    # Authorization: Students can only view their own evidence; coordinators can view all
    if current_user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile or evidence.student_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view your own evidence."
            )

    return EvidenceDetailResponse(
        id=evidence.id,
        student_id=evidence.student_id,
        type=evidence.type,
        original_filename=evidence.original_filename,
        authenticity_state=evidence.authenticity_state,
        extracted_metadata=evidence.extracted_metadata,
        mapped_skills=evidence.mapped_skills,
        created_at=evidence.created_at,
        download_url=f"/api/v1/evidence/{evidence.id}/download"
    )


@router.get("/{evidence_id}/download")
def download_evidence_file(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely download the evidence file with strict ownership checks."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found."
        )

    # Ownership check
    if current_user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile or evidence.student_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only download your own evidence files."
            )

    if not evidence.file_path or not Path(evidence.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found on storage."
        )

    mime_type = (evidence.extracted_metadata or {}).get("mime_type", "application/octet-stream")

    return FileResponse(
        path=evidence.file_path,
        filename=evidence.original_filename or "document",
        media_type=mime_type
    )


@router.delete("/{evidence_id}", response_model=MessageResponse)
def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Delete an evidence record and its underlying stored file.
    Cannot delete evidence that has been marked INSTITUTION_VERIFIED.
    Automatically recomputes skill verification status via the deterministic engine.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    evidence = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.student_id == profile.id
    ).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found."
        )

    if evidence.authenticity_state == AuthenticityState.INSTITUTION_VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete evidence that has been verified by the placement institution."
        )

    mapped_skills = list(evidence.mapped_skills or [])
    file_path = evidence.file_path

    # Delete database record
    db.delete(evidence)
    db.commit()

    # Safely delete underlying file
    if file_path:
        delete_file(file_path)

    # Recompute student skill status for affected skills
    for skill_name in mapped_skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            update_and_persist_skill_status(profile.id, skill.id, db)

    return MessageResponse(message="Evidence successfully deleted and skill statuses recomputed.")


@router.patch("/{evidence_id}/verify", response_model=EvidenceResponse)
def verify_evidence(
    evidence_id: str,
    payload: EvidenceVerifyRequest,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Placement Coordinator verification endpoint to set INSTITUTION_VERIFIED state."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found."
        )

    if payload.authenticity_state != AuthenticityState.INSTITUTION_VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target authenticity state must be '{AuthenticityState.INSTITUTION_VERIFIED.value}'."
        )

    evidence.authenticity_state = AuthenticityState.INSTITUTION_VERIFIED

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="EVIDENCE_INSTITUTION_VERIFIED",
        details=f"Coordinator {current_user.email} verified evidence {evidence.id}. Remarks: {payload.remarks or 'None'}"
    )
    db.add(audit)
    db.commit()
    db.refresh(evidence)

    return evidence
