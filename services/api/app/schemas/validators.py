"""
Reusable input validation functions for ProofPath.
Enforces type, format, length, range, and character constraints across all endpoints.
"""

import math
import re
from typing import List, Dict, Optional

MVP_SKILLS = ["Python", "Pandas", "Matplotlib", "Git/GitHub"]
VALID_VERIFICATION_LEVELS = ["UNVERIFIED", "EVIDENCE_SUPPORTED", "SKILL_ASSESSED", "SKILL_VERIFIED"]


def validate_full_name(v: str) -> str:
    """
    Validate full name:
    - 2 to 80 characters
    - Must contain at least 2 letters
    - Letters, spaces, apostrophes, hyphens, and periods allowed
    - Digits and special symbols strictly rejected
    """
    if v is None:
        raise ValueError("Full name is required.")
    v = v.strip()
    if len(v) < 2 or len(v) > 80:
        raise ValueError("Full name must be between 2 and 80 characters.")

    if re.search(r"\d", v):
        raise ValueError("Full name cannot contain numbers.")

    if not re.match(r"^[a-zA-Z\s'\-\.]+$", v):
        raise ValueError("Full name can only contain letters, spaces, hyphens, apostrophes, and periods.")

    letters = re.findall(r"[a-zA-Z]", v)
    if len(letters) < 2:
        raise ValueError("Full name must contain at least 2 alphabetic characters.")

    return v


def validate_college_name(v: str) -> str:
    """
    Validate college or institution name:
    - 2 to 120 characters
    - Letters, numbers, spaces, and institutional punctuation (&, ., -, ', /, ())
    - Must contain at least 2 alphanumeric characters
    """
    if v is None:
        raise ValueError("College/institution name is required.")
    v = v.strip()
    if len(v) < 2 or len(v) > 120:
        raise ValueError("College/institution name must be between 2 and 120 characters.")

    if not re.match(r"^[a-zA-Z0-9\s&.\-'\/\(\)]+$", v):
        raise ValueError("College/institution name contains invalid characters.")

    alnum = re.findall(r"[a-zA-Z0-9]", v)
    if len(alnum) < 2:
        raise ValueError("College/institution name must contain at least 2 alphanumeric characters.")

    return v


def validate_branch(v: str) -> str:
    """
    Validate academic branch/major:
    - 2 to 80 characters
    - Letters, numbers, spaces, and academic punctuation (&, /, -, .)
    - Must contain at least 2 alphanumeric characters
    """
    if v is None:
        raise ValueError("Branch/major is required.")
    v = v.strip()
    if len(v) < 2 or len(v) > 80:
        raise ValueError("Branch/major must be between 2 and 80 characters.")

    if not re.match(r"^[a-zA-Z0-9\s&/\-\.]+$", v):
        raise ValueError("Branch/major contains invalid characters.")

    alnum = re.findall(r"[a-zA-Z0-9]", v)
    if len(alnum) < 2:
        raise ValueError("Branch/major must contain at least 2 alphanumeric characters.")

    return v


def validate_academic_year(v: int) -> int:
    """
    Validate graduation year:
    - 4-digit integer
    - Range: 2000 to 2040
    """
    if v is None:
        raise ValueError("Graduation year is required.")
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("Graduation year must be an integer.")
    if v < 2000 or v > 2040:
        raise ValueError("Graduation year must be a 4-digit year between 2000 and 2040.")
    return v


def validate_cgpa(v: float) -> float:
    """
    Validate cumulative GPA (CGPA):
    - Real numeric value
    - Range: 0.00 to 10.00
    - Maximum 2 decimal places
    """
    if v is None:
        raise ValueError("CGPA is required.")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ValueError("CGPA must be a valid numeric value.")
    if math.isnan(v) or math.isinf(v):
        raise ValueError("CGPA must be a valid real number.")
    if v < 0.0 or v > 10.0:
        raise ValueError("CGPA must be between 0.00 and 10.00.")

    # Check for excessive decimal precision beyond 2 decimal places
    if round(v, 2) != round(v, 6):
        raise ValueError("CGPA cannot have more than 2 decimal places.")

    return round(float(v), 2)


def validate_claimed_skills(v: Optional[List[str]]) -> Optional[List[str]]:
    """
    Validate student claimed skills:
    - If provided, must be non-empty
    - Must only contain valid ProofPath MVP skills
    - Deduplicates entries while preserving order
    """
    if v is None:
        return None

    if len(v) == 0:
        raise ValueError("At least one claimed MVP skill must be selected.")

    deduped: List[str] = []
    seen = set()
    for item in v:
        if not isinstance(item, str):
            raise ValueError("Each skill must be a string.")
        cleaned = item.strip()
        if cleaned not in MVP_SKILLS:
            raise ValueError(f"Unknown skill '{cleaned}'. Allowed MVP skills: {', '.join(MVP_SKILLS)}.")
        if cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)

    return deduped


def validate_company_name(v: str) -> str:
    """
    Validate company name for placement requirements:
    - 2 to 120 characters
    - Alphanumeric, spaces, and business punctuation (&, ., -, ', ,, /, ())
    - Must contain at least 2 alphanumeric characters
    """
    if v is None:
        raise ValueError("Company name is required.")
    v = v.strip()
    if len(v) < 2 or len(v) > 120:
        raise ValueError("Company name must be between 2 and 120 characters.")

    if not re.match(r"^[a-zA-Z0-9\s&.\-',/\(\)]+$", v):
        raise ValueError("Company name contains invalid characters.")

    alnum = re.findall(r"[a-zA-Z0-9]", v)
    if len(alnum) < 2:
        raise ValueError("Company name must contain at least 2 alphanumeric characters.")

    return v


def validate_role_title(v: str) -> str:
    """
    Validate role title for placement requirements:
    - 2 to 100 characters
    - Alphanumeric, spaces, and common role punctuation (&, /, -, ., ())
    - Must contain at least 2 alphanumeric characters
    """
    if v is None:
        raise ValueError("Role title is required.")
    v = v.strip()
    if len(v) < 2 or len(v) > 100:
        raise ValueError("Role title must be between 2 and 100 characters.")

    if not re.match(r"^[a-zA-Z0-9\s&/\-\.\(\)]+$", v):
        raise ValueError("Role title contains invalid characters.")

    alnum = re.findall(r"[a-zA-Z0-9]", v)
    if len(alnum) < 2:
        raise ValueError("Role title must contain at least 2 alphanumeric characters.")

    return v


def validate_eligible_branches(v: List[str]) -> List[str]:
    """
    Validate list of eligible branches:
    - Each branch must satisfy branch validation rules
    - Empty branches rejected
    - Deduplicates list
    """
    if not isinstance(v, list):
        raise ValueError("Eligible branches must be a list.")

    deduped: List[str] = []
    seen = set()
    for b in v:
        if not isinstance(b, str) or not b.strip():
            continue
        validated = validate_branch(b)
        if validated not in seen:
            seen.add(validated)
            deduped.append(validated)

    return deduped


def validate_required_skills(v: Dict[str, str]) -> Dict[str, str]:
    """
    Validate required skills map for placement requirement:
    - Key must be one of the 4 MVP skills
    - Value must be a recognized verification level
    """
    if not isinstance(v, dict):
        raise ValueError("Required skills must be an object/dictionary.")

    normalized: Dict[str, str] = {}
    for skill_name, level in v.items():
        clean_name = skill_name.strip()
        if clean_name not in MVP_SKILLS:
            raise ValueError(f"Unknown required skill '{clean_name}'. Allowed MVP skills: {', '.join(MVP_SKILLS)}.")

        clean_level = level.strip().upper()
        if clean_level not in VALID_VERIFICATION_LEVELS:
            raise ValueError(f"Invalid verification level '{level}' for skill '{clean_name}'. Allowed: {', '.join(VALID_VERIFICATION_LEVELS)}.")

        normalized[clean_name] = clean_level

    return normalized
