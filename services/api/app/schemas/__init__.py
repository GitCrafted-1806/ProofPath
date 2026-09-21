from app.schemas.common import MessageResponse
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.student import StudentSkillResponse, StudentProfileResponse
from app.schemas.evidence import (
    EvidenceUploadType,
    EvidenceMetadataSchema,
    EvidenceResponse,
    EvidenceDetailResponse,
    EvidenceVerifyRequest,
)
from app.schemas.github import (
    GitHubConnectionStatusResponse,
    GitHubOAuthStartResponse,
    GitHubRepositoryResponse,
    GitHubRepoSelectRequest,
    GitHubRepoEvidenceResponse,
)

__all__ = [
    "MessageResponse",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "StudentSkillResponse",
    "StudentProfileResponse",
    "EvidenceUploadType",
    "EvidenceMetadataSchema",
    "EvidenceResponse",
    "EvidenceDetailResponse",
    "EvidenceVerifyRequest",
    "GitHubConnectionStatusResponse",
    "GitHubOAuthStartResponse",
    "GitHubRepositoryResponse",
    "GitHubRepoSelectRequest",
    "GitHubRepoEvidenceResponse",
]
