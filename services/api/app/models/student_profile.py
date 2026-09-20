import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_public_profile_id() -> str:
    """Generate a non-guessable, URL-safe public profile token."""
    return f"prf_{secrets.token_urlsafe(16)}"


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    qualification = Column(String(100), nullable=False, default="B.Tech")
    college_name = Column(String(255), nullable=False)
    branch = Column(String(100), nullable=False)
    academic_year = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=False, default=0.0)
    public_profile_id = Column(String(64), unique=True, index=True, default=generate_public_profile_id, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="student_profile")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
