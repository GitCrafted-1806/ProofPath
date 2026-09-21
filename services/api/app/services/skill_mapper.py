import re
from typing import List
from app.models.skill import MVP_SKILLS

# Regex mapping for the 4 MVP skills using word boundaries to prevent false positives
SKILL_PATTERNS = {
    "Python": re.compile(r'\b(python|python3|py)\b', re.IGNORECASE),
    "Pandas": re.compile(r'\b(pandas|dataframe[s]?)\b', re.IGNORECASE),
    "Matplotlib": re.compile(r'\b(matplotlib|pyplot)\b', re.IGNORECASE),
    "Git/GitHub": re.compile(r'\b(git|github|version\s+control)\b', re.IGNORECASE),
}


def map_skills_from_text(text: str) -> List[str]:
    """
    Deterministic regex-based skill mapping strictly to MVP skills:
    - Python
    - Pandas
    - Matplotlib
    - Git/GitHub
    
    Uses exact word boundaries (\\b) to avoid false-positive matches (e.g., 'digit' will not match 'git').
    Returns a sorted list of unique canonical MVP skill names.
    """
    if not text:
        return []

    matched_skills = []
    for skill_name in MVP_SKILLS:
        pattern = SKILL_PATTERNS.get(skill_name)
        if pattern and pattern.search(text):
            matched_skills.append(skill_name)

    return matched_skills
