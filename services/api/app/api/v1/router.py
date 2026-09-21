from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.github import router as github_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.demo import router as demo_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(students_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(github_router)
api_v1_router.include_router(assessments_router)
api_v1_router.include_router(demo_router)
