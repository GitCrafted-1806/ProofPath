from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.student_skill import SkillVerificationStatus


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    NUMERICAL_INPUT = "NUMERICAL_INPUT"
    CODE_OUTPUT = "CODE_OUTPUT"


class AssessmentQuestionClientSchema(BaseModel):
    """Client-facing question schema (CRITICAL: correct_answer is strictly omitted!)."""
    id: str
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    code_snippet: Optional[str] = None
    points: float = 1.0


class AssessmentStartRequest(BaseModel):
    """Payload to initiate an assessment for a skill."""
    skill_id: str
    type: str = "PRACTICAL"  # PRACTICAL or FOLLOW_UP


class AssessmentTakeResponse(BaseModel):
    """Active assessment presented to the student (answers masked)."""
    id: str
    student_id: str
    skill_id: str
    skill_name: str
    type: str
    status: str
    questions: List[AssessmentQuestionClientSchema]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


from pydantic import field_validator


class AssessmentSubmitRequest(BaseModel):
    """Student submission payload."""
    answers: Dict[str, Any] = Field(..., description="Mapping of question id to submitted answer")

    @field_validator("answers")
    @classmethod
    def check_answers(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Answers payload must be a dictionary.")
        if len(v) > 50:
            raise ValueError("Answers payload contains too many items (maximum 50).")
        for q_id, ans in v.items():
            if not isinstance(q_id, str) or len(q_id) < 1 or len(q_id) > 100:
                raise ValueError("Invalid question ID format.")
            if isinstance(ans, str) and len(ans) > 500:
                raise ValueError(f"Answer for question '{q_id}' exceeds maximum length of 500 characters.")
        return v



class QuestionResultFeedback(BaseModel):
    """Detailed result feedback per question revealed after submission."""
    question_id: str
    question: str
    submitted_answer: Any
    correct_answer: Any
    is_correct: bool
    explanation: Optional[str] = None


class AssessmentResultResponse(BaseModel):
    """Result returned after evaluating an assessment submission."""
    id: str
    student_id: str
    skill_id: str
    skill_name: str
    type: str
    status: str
    score: float
    passed: bool
    evaluation_summary: str
    completed_at: datetime
    feedback: List[QuestionResultFeedback]
    new_skill_status: SkillVerificationStatus

    model_config = ConfigDict(from_attributes=True)


class SkillAssessmentAvailabilityResponse(BaseModel):
    """Summary of which assessments are available for a given skill based on evidence prerequisites."""
    skill_id: str
    skill_name: str
    current_status: SkillVerificationStatus
    practical_available: bool
    followup_available: bool
    pending_assessment_id: Optional[str] = None
    reason: Optional[str] = None


class AssessmentHistoryItemResponse(BaseModel):
    """Historical assessment summary item."""
    id: str
    skill_id: str
    skill_name: str
    type: str
    status: str
    score: Optional[float] = None
    passed: bool
    evaluation_summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
