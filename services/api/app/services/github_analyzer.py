import re
from typing import Dict, Any, List, Tuple
from app.models.skill import MVP_SKILLS


def analyze_repository_evidence(repo_details: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Lightweight deterministic analysis of a GitHub repository to extract signals and map to MVP skills:
    - Python
    - Pandas
    - Matplotlib
    - Git/GitHub
    
    Returns:
        Tuple of (mapped_skills: List[str], structured_metadata: Dict[str, Any])
    """
    language = (repo_details.get("language") or "").strip().lower()
    description = (repo_details.get("description") or "").lower()
    topics = [str(t).strip().lower() for t in repo_details.get("topics", [])]
    dependencies = [str(d).strip().lower() for d in repo_details.get("dependencies", [])]
    readme = (repo_details.get("readme_content") or "").lower()
    files = [str(f).strip().lower() for f in repo_details.get("files", [])]

    # Combine textual search space for dependencies and keywords
    combined_dep_text = " ".join(dependencies)
    combined_topics = " ".join(topics)

    detected_signals: Dict[str, Any] = {
        "primary_language": repo_details.get("language"),
        "matched_criteria": []
    }

    mapped_skills: List[str] = []

    # 1. Git/GitHub: Any valid repository selected via GitHub API is Git/GitHub version-controlled project evidence
    mapped_skills.append("Git/GitHub")
    detected_signals["matched_criteria"].append("Git/GitHub: GitHub repository integration")

    # 2. Python signal detection
    is_python = (
        language == "python"
        or "python" in topics
        or "python3" in topics
        or any(f.endswith(".py") for f in files)
        or re.search(r'\b(python|python3)\b', description)
        or re.search(r'\bpython\b', readme)
    )
    if is_python:
        mapped_skills.append("Python")
        detected_signals["matched_criteria"].append("Python: detected in language/topics/files")

    # 3. Pandas signal detection
    has_pandas = (
        "pandas" in topics
        or "pandas" in combined_dep_text
        or re.search(r'\bpandas\b', description)
        or re.search(r'\bpandas\b', readme)
    )
    if has_pandas:
        mapped_skills.append("Pandas")
        detected_signals["matched_criteria"].append("Pandas: detected in topics/dependencies/README")

    # 4. Matplotlib signal detection
    has_matplotlib = (
        "matplotlib" in topics
        or "matplotlib" in combined_dep_text
        or re.search(r'\bmatplotlib\b', description)
        or re.search(r'\bmatplotlib\b', readme)
    )
    if has_matplotlib:
        mapped_skills.append("Matplotlib")
        detected_signals["matched_criteria"].append("Matplotlib: detected in topics/dependencies/README")

    # Deduplicate and sort mapped skills
    mapped_skills = sorted(list(set(s for s in mapped_skills if s in MVP_SKILLS)))

    # Structure metadata for Evidence.extracted_metadata
    metadata = {
        "repo_id": repo_details.get("id"),
        "repo_name": repo_details.get("name"),
        "full_name": repo_details.get("full_name"),
        "owner": repo_details.get("owner"),
        "description": repo_details.get("description"),
        "html_url": repo_details.get("html_url"),
        "default_branch": repo_details.get("default_branch", "main"),
        "language": repo_details.get("language"),
        "stars": repo_details.get("stars", 0),
        "forks": repo_details.get("forks", 0),
        "is_private": repo_details.get("is_private", False),
        "topics": repo_details.get("topics", []),
        "updated_at": repo_details.get("updated_at"),
        "detected_signals": detected_signals,
    }

    return mapped_skills, metadata
