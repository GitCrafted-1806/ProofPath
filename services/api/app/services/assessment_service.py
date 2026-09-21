"""Deterministic assessment service for question delivery, answer masking, and score evaluation."""
from typing import Dict, List, Any, Tuple
import copy

from app.mock_data.assessment_fixtures import ASSESSMENT_FIXTURES
from app.schemas.assessment import AssessmentQuestionClientSchema, QuestionType


def get_assessment_questions(skill_name: str, assessment_type: str) -> List[Dict[str, Any]]:
    """
    Retrieve questions for a given skill and assessment type.
    Falls back to case-insensitive skill matching if needed.
    """
    normalized_type = assessment_type.upper()
    if normalized_type not in ("PRACTICAL", "FOLLOW_UP"):
        raise ValueError(f"Invalid assessment type '{assessment_type}'. Must be PRACTICAL or FOLLOW_UP.")

    # Match skill name directly or case-insensitively
    skill_fixtures = ASSESSMENT_FIXTURES.get(skill_name)
    if not skill_fixtures:
        for k, v in ASSESSMENT_FIXTURES.items():
            if k.lower() == skill_name.lower():
                skill_fixtures = v
                break

    if not skill_fixtures or normalized_type not in skill_fixtures:
        raise ValueError(f"No assessment questions available for skill '{skill_name}' and type '{normalized_type}'.")

    # Return deep copy so in-memory fixtures are never accidentally mutated
    return copy.deepcopy(skill_fixtures[normalized_type])


def mask_questions_for_client(questions: List[Dict[str, Any]]) -> List[AssessmentQuestionClientSchema]:
    """
    Mask assessment questions for student view.
    CRITICAL SECURITY RULE: Strips `correct_answer` and `explanation` so answers are never exposed.
    """
    masked = []
    for q in questions:
        masked.append(
            AssessmentQuestionClientSchema(
                id=str(q["id"]),
                question=str(q["question"]),
                type=QuestionType(q["type"]),
                options=q.get("options"),
                code_snippet=q.get("code_snippet"),
                points=float(q.get("points", 1.0)),
            )
        )
    return masked


def evaluate_assessment_submission(
    questions: List[Dict[str, Any]],
    submitted_answers: Dict[str, Any],
) -> Tuple[float, bool, List[Dict[str, Any]], str]:
    """
    Deterministically evaluates student submission against stored assessment questions.
    Returns:
        (score, passed, feedback_list, summary)
    Threshold: score >= 70.0% is passed.
    """
    if not questions:
        return 0.0, False, [], "No questions in assessment."

    total_points_possible = 0.0
    points_earned = 0.0
    feedback_list: List[Dict[str, Any]] = []

    for q in questions:
        q_id = str(q["id"])
        q_points = float(q.get("points", 1.0))
        total_points_possible += q_points

        correct_ans = q.get("correct_answer")
        submitted_ans = submitted_answers.get(q_id)
        q_type = q.get("type")

        is_correct = False

        if submitted_ans is not None:
            if q_type == QuestionType.NUMERICAL_INPUT.value or isinstance(correct_ans, (int, float)):
                try:
                    num_sub = float(str(submitted_ans).strip())
                    num_corr = float(correct_ans)
                    if abs(num_sub - num_corr) < 1e-4:
                        is_correct = True
                except (ValueError, TypeError):
                    is_correct = False
            else:
                # String comparison
                str_sub = str(submitted_ans).strip()
                str_corr = str(correct_ans).strip()
                if q_type == QuestionType.MULTIPLE_CHOICE.value:
                    is_correct = str_sub.lower() == str_corr.lower()
                else:
                    # CODE_OUTPUT or exact text match
                    is_correct = str_sub == str_corr

        if is_correct:
            points_earned += q_points

        feedback_list.append(
            {
                "question_id": q_id,
                "question": q.get("question", ""),
                "submitted_answer": submitted_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "explanation": q.get("explanation"),
            }
        )

    score = round((points_earned / total_points_possible) * 100.0, 1) if total_points_possible > 0 else 0.0
    passed = score >= 70.0

    total_q_count = len(questions)
    correct_q_count = sum(1 for f in feedback_list if f["is_correct"])

    if passed:
        summary = f"Scored {score:.1f}% ({correct_q_count}/{total_q_count} questions correct). Assessment passed."
    else:
        summary = f"Scored {score:.1f}% ({correct_q_count}/{total_q_count} questions correct). Passing score is 70.0%."

    return score, passed, feedback_list, summary
