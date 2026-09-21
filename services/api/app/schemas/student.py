from datetime import datetime
from typing import List, Optional
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


from app.schemas.validators import (
    validate_full_name,
    validate_college_name,
    validate_branch,
    validate_academic_year,
    validate_cgpa,
    validate_claimed_skills,
)
from pydantic import field_validator


class StudentProfileUpdateRequest(BaseModel):
    """Payload for updating student profile fields."""
    full_name: Optional[str] = None
    qualification: Optional[str] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    academic_year: Optional[int] = None
    cgpa: Optional[float] = None
    is_public: Optional[bool] = None
    skills: Optional[List[str]] = None

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v):
        if v is not None:
            return validate_full_name(v)
        return v

    @field_validator("college_name")
    @classmethod
    def check_college(cls, v):
        if v is not None:
            return validate_college_name(v)
        return v

    @field_validator("branch")
    @classmethod
    def check_branch(cls, v):
        if v is not None:
            return validate_branch(v)
        return v

    @field_validator("academic_year")
    @classmethod
    def check_year(cls, v):
        if v is not None:
            return validate_academic_year(v)
        return v

    @field_validator("cgpa")
    @classmethod
    def check_cgpa(cls, v):
        if v is not None:
            return validate_cgpa(v)
        return v

    @field_validator("skills")
    @classmethod
    def check_skills(cls, v):
        return validate_claimed_skills(v)



class PublicStudentProfileResponse(BaseModel):
    """Publicly sharable student verification profile (omits user_id and email)."""
    id: str
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


class StudentDirectoryItemResponse(BaseModel):
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
    skills_count: int = 0
    verified_skills_count: int = 0
    skills: List[StudentSkillResponse] = []

    model_config = ConfigDict(from_attributes=True)


class StudentDirectoryListResponse(BaseModel):
    total: int
    students: List[StudentDirectoryItemResponse]

