import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class GitHubAccount(Base):
    __tablename__ = "github_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    github_user_id = Column(String(100), nullable=False)
    github_username = Column(String(100), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    profile_url = Column(String(512), nullable=True)
    encrypted_access_token = Column(String(512), nullable=True)
    scopes = Column(String(255), default="read:user,repo", nullable=False)
    connected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    student = relationship("StudentProfile", back_populates="github_account")
