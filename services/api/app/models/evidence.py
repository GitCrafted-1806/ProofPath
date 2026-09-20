import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class EvidenceType(str, Enum):
    CERTIFICATE = "CERTIFICATE"
    PROJECT_DOCUMENT = "PROJECT_DOCUMENT"
    GITHUB_REPO = "GITHUB_REPO"


class AuthenticityState(str, Enum):
    SUBMITTED = "SUBMITTED"
    SOURCE_SUPPORTED = "SOURCE_SUPPORTED"
    INSTITUTION_VERIFIED = "INSTITUTION_VERIFIED"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(EvidenceType), nullable=False)
    file_path = Column(String(512), nullable=True)
    original_filename = Column(String(255), nullable=True)
    authenticity_state = Column(
        SQLEnum(AuthenticityState),
        default=AuthenticityState.SUBMITTED,
        nullable=False
    )
    extracted_metadata = Column(JSON, default=dict, nullable=False)
    mapped_skills = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student = relationship("StudentProfile", back_populates="evidence")
