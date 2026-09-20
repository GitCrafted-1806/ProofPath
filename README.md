# ProofPath

> **"Don't just claim your skills. Prove them."**

ProofPath is an evidence-based campus placement platform designed to verify student skills using verifiable artifacts, deterministic evaluation rules, and practical assessments rather than self-reported resume claims.

---

## Architecture Overview

### User-Facing Interfaces (Phases 5 & 6)
1. **Student Mobile Application** (`apps/student-mobile`): React Native, Expo, TypeScript.
2. **College Placement Cell Web Dashboard** (`apps/placement-web`): Next.js, App Router, TypeScript.

### Backend Foundation (Phase 1)
* **Framework**: FastAPI (Python 3.12+)
* **Database & ORM**: SQLite (development) / PostgreSQL compatible, SQLAlchemy 2.0
* **Validation**: Pydantic v2
* **Security**: JWT Authentication, bcrypt password hashing, strict RBAC
* **Engine**: Deterministic rules-based verification engine (zero opaque AI scoring)

---

## Phase 1 Quickstart

### 1. Environment Setup
```bash
cd services/api
python -m venv venv
```

On Windows (PowerShell):
```powershell
venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
pytest
```

### 4. Start Local Development Server
```bash
uvicorn main:app --reload --port 8000
```

Access Interactive Documentation at:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
* Demo Status: [http://localhost:8000/api/v1/demo/status](http://localhost:8000/api/v1/demo/status)
