from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.services.demo_seed import seed_demo_data
from app.api.v1.router import api_v1_router
from app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database schemas and conditional demo seeding."""
    init_db()

    if settings.DEMO_MODE:
        db = SessionLocal()
        try:
            # Check if demo data already seeded
            user_count = db.query(User).count()
            if user_count == 0:
                seed_demo_data(db)
        finally:
            db.close()

    yield


app = FastAPI(
    title="ProofPath API",
    description="Evidence-Based Campus Placement Verification Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint confirming service status."""
    return {
        "status": "healthy",
        "service": "ProofPath API",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE
    }


# Include API v1 routes
app.include_router(api_v1_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
