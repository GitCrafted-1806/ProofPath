import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), default="PRACTICAL", nullable=False)  # PRACTICAL, FOLLOW_UP
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, COMPLETED, FAILED
    score = Column(Float, nullable=True)
    passed = Column(Boolean, default=False, nullable=False)
    evaluation_summary = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("StudentProfile", back_populates="assessments")
    skill = relationship("Skill", back_populates="assessments")
