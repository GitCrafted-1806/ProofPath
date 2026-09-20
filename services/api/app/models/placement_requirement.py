import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlacementRequirement(Base):
    __tablename__ = "placement_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    coordinator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=False)
    min_cgpa = Column(Float, nullable=False, default=6.0)
    eligible_branches = Column(JSON, default=list, nullable=False)  # e.g. ["CSE", "IT"]
    required_skills = Column(JSON, default=dict, nullable=False)    # e.g. {"Python": "SKILL_VERIFIED", "Pandas": "SKILL_ASSESSED"}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    coordinator = relationship("User", back_populates="placement_requirements")
