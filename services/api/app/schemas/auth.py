from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: UserRole = Field(default=UserRole.STUDENT)
    
    # Optional profile details for students during registration
    full_name: Optional[str] = "Student User"
    qualification: Optional[str] = "B.Tech"
    college_name: Optional[str] = "National Institute of Technology"
    branch: Optional[str] = "CSE"
    academic_year: Optional[int] = 2026
    cgpa: Optional[float] = Field(default=7.5, ge=0.0, le=10.0)


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
