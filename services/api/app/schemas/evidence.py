from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.evidence import EvidenceType, AuthenticityState


class EvidenceUploadType(str, Enum):
    """Allowed evidence types for file uploads in Phase 2."""
    CERTIFICATE = "CERTIFICATE"
    PROJECT_DOCUMENT = "PROJECT_DOCUMENT"


class EvidenceMetadataSchema(BaseModel):
    """Structured schema for extracted evidence metadata."""
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    credential_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_name_matched: bool = False
    extraction_method: str = "PYMUPDF_TEXT"
    file_size: int = Field(..., ge=0)
    mime_type: str
    sha256: str
    text_snippet: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)


class EvidenceResponse(BaseModel):
    """API response schema for evidence records."""
    id: str
    student_id: str
    type: EvidenceType
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    authenticity_state: AuthenticityState
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    mapped_skills: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceDetailResponse(EvidenceResponse):
    """Detailed evidence response including download URL."""
    download_url: str


class EvidenceVerifyRequest(BaseModel):
    """Coordinator payload to verify institutional authenticity."""
    authenticity_state: AuthenticityState = AuthenticityState.INSTITUTION_VERIFIED
    remarks: Optional[str] = None
