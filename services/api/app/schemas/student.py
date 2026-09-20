from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict
from app.models.student_skill import SkillVerificationStatus


class StudentSkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    verification_status: SkillVerificationStatus
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentProfileResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    qualification: str
    college_name: str
    branch: str
    academic_year: int
    cgpa: float
    public_profile_id: str
    is_public: bool
    skills: List[StudentSkillResponse] = []

    model_config = ConfigDict(from_attributes=True)
