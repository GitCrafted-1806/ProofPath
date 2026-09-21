from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.user import UserRole
from app.schemas.validators import (
    validate_full_name,
    validate_college_name,
    validate_branch,
    validate_academic_year,
    validate_cgpa,
    validate_claimed_skills,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")
    role: UserRole = Field(default=UserRole.STUDENT)

    # Profile details for students during registration
    full_name: Optional[str] = None
    qualification: Optional[str] = "B.Tech"
    college_name: Optional[str] = None
    branch: Optional[str] = None
    academic_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = None

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

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



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
