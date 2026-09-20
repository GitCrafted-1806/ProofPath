import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class SkillVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    EVIDENCE_SUPPORTED = "EVIDENCE_SUPPORTED"
    SKILL_ASSESSED = "SKILL_ASSESSED"
    SKILL_VERIFIED = "SKILL_VERIFIED"


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    verification_status = Column(
        SQLEnum(SkillVerificationStatus),
        default=SkillVerificationStatus.UNVERIFIED,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Composite unique constraint: a student can have only one record per skill
    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )

    # Relationships
    student = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill", back_populates="student_skills")
