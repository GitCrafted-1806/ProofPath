from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


from app.schemas.validators import (
    validate_company_name,
    validate_role_title,
    validate_cgpa,
    validate_eligible_branches,
    validate_required_skills,
)
from pydantic import field_validator


class PlacementRequirementCreateRequest(BaseModel):
    company_name: str
    role_title: str
    min_cgpa: float = Field(default=6.0, ge=0.0, le=10.0)
    eligible_branches: List[str] = Field(default_factory=list)
    required_skills: Dict[str, str] = Field(default_factory=dict)

    @field_validator("company_name")
    @classmethod
    def check_company(cls, v):
        return validate_company_name(v)

    @field_validator("role_title")
    @classmethod
    def check_role(cls, v):
        return validate_role_title(v)

    @field_validator("min_cgpa")
    @classmethod
    def check_cgpa(cls, v):
        return validate_cgpa(v)

    @field_validator("eligible_branches")
    @classmethod
    def check_branches(cls, v):
        return validate_eligible_branches(v)

    @field_validator("required_skills")
    @classmethod
    def check_skills(cls, v):
        return validate_required_skills(v)



class PlacementRequirementResponse(BaseModel):
    id: str
    coordinator_id: str
    company_name: str
    role_title: str
    min_cgpa: float
    eligible_branches: List[str]
    required_skills: Dict[str, str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateMatchItem(BaseModel):
    student_id: str
    full_name: str
    email: str
    college_name: Optional[str] = None
    branch: str
    academic_year: Optional[int] = None
    cgpa: float
    is_matched: bool
    criteria_results: Dict[str, Any]
    failure_reasons: List[str] = []
    skills: Dict[str, str] = {}


class PlacementMatchResponse(BaseModel):
    requirement: PlacementRequirementResponse
    total_candidates: int
    matched_count: int
    unmatched_count: int
    matches: List[CandidateMatchItem]


class AssessmentRequestCoordinatorPayload(BaseModel):
    student_id: str
    skill_id: str
    type: str = "PRACTICAL"


class AssessmentRequestCoordinatorResponse(BaseModel):
    status: str
    message: str
    assessment_id: Optional[str] = None
    student_id: str
    skill_id: str
    type: str
