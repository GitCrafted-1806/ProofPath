"""Mock fixtures and demo seed data definitions."""
DEMO_COORDINATOR = {
    "email": "coordinator@college.edu",
    "password": "Password123!",
    "role": "PLACEMENT_COORDINATOR"
}

DEMO_STUDENTS = [
    {
        "email": "john.doe@nit.edu",
        "password": "Password123!",
        "full_name": "John Doe",
        "qualification": "B.Tech",
        "college_name": "National Institute of Technology",
        "branch": "CSE",
        "academic_year": 2026,
        "cgpa": 8.2,
        "skill_states": {
            "Python": "SKILL_VERIFIED",
            "Pandas": "SKILL_ASSESSED",
            "Matplotlib": "EVIDENCE_SUPPORTED",
            "Git/GitHub": "EVIDENCE_SUPPORTED",
        },
        "project_name": "Student Performance Analyzer",
        "project_skills": ["Python", "Pandas"]
    },
    {
        "email": "jane.smith@nit.edu",
        "password": "Password123!",
        "full_name": "Jane Smith",
        "qualification": "B.Tech",
        "college_name": "National Institute of Technology",
        "branch": "IT",
        "academic_year": 2026,
        "cgpa": 8.8,
        "skill_states": {
            "Python": "SKILL_ASSESSED",
            "Pandas": "SKILL_VERIFIED",
            "Matplotlib": "SKILL_ASSESSED",
            "Git/GitHub": "EVIDENCE_SUPPORTED",
        },
        "project_name": "Pandas Financial Forecasting",
        "project_skills": ["Pandas"]
    },
    {
        "email": "alex.kumar@nit.edu",
        "password": "Password123!",
        "full_name": "Alex Kumar",
        "qualification": "B.Tech",
        "college_name": "National Institute of Technology",
        "branch": "ECE",
        "academic_year": 2026,
        "cgpa": 7.4,
        "skill_states": {
            "Python": "EVIDENCE_SUPPORTED",
            "Pandas": "UNVERIFIED",
            "Matplotlib": "UNVERIFIED",
            "Git/GitHub": "EVIDENCE_SUPPORTED",
        },
        "project_name": None,
        "project_skills": []
    },
    {
        "email": "priya.sharma@nit.edu",
        "password": "Password123!",
        "full_name": "Priya Sharma",
        "qualification": "B.Tech",
        "college_name": "National Institute of Technology",
        "branch": "CSE",
        "academic_year": 2026,
        "cgpa": 9.1,
        "skill_states": {
            "Python": "SKILL_VERIFIED",
            "Pandas": "SKILL_VERIFIED",
            "Matplotlib": "SKILL_VERIFIED",
            "Git/GitHub": "SKILL_VERIFIED",
        },
        "project_name": "Full Stack Analytics & Visualization Engine",
        "project_skills": ["Python", "Pandas", "Matplotlib", "Git/GitHub"]
    }
]
