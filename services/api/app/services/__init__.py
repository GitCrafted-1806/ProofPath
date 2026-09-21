"""Services package for verification, evidence storage, document processing, and demo seeding."""
from app.services.verification_engine import (
    compute_skill_status,
    update_and_persist_skill_status,
    check_skill_prerequisites,
)
from app.services.file_storage import (
    save_upload_file,
    delete_file,
    validate_file_header,
    sanitize_filename,
)
from app.services.document_parser import (
    parse_document,
    extract_text_from_pdf,
    extract_text_from_image,
    is_tesseract_available,
)
from app.services.text_sanitizer import (
    normalize_document_text,
)
from app.services.skill_mapper import (
    map_skills_from_text,
)
from app.services.metadata_extractor import (
    extract_document_metadata,
)
from app.services.github_service import (
    create_oauth_state,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_student_repositories,
    fetch_repository_details,
)
from app.services.github_analyzer import (
    analyze_repository_evidence,
)

__all__ = [
    "compute_skill_status",
    "update_and_persist_skill_status",
    "check_skill_prerequisites",
    "save_upload_file",
    "delete_file",
    "validate_file_header",
    "sanitize_filename",
    "parse_document",
    "extract_text_from_pdf",
    "extract_text_from_image",
    "is_tesseract_available",
    "normalize_document_text",
    "map_skills_from_text",
    "extract_document_metadata",
    "create_oauth_state",
    "validate_oauth_state",
    "exchange_code_for_token",
    "fetch_student_repositories",
    "fetch_repository_details",
    "analyze_repository_evidence",
]
