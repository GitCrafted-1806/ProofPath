from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import EvidenceResponse


class GitHubConnectionStatusResponse(BaseModel):
    """Schema for GitHub connection status (never exposes access token)."""
    is_connected: bool
    github_username: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None
    connected_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GitHubOAuthStartResponse(BaseModel):
    """Response schema when initiating GitHub OAuth flow."""
    authorize_url: str
    state: str
    demo_mode: bool


class GitHubRepositoryResponse(BaseModel):
    """Normalized GitHub repository schema."""
    id: int
    name: str
    full_name: str
    owner: str
    description: Optional[str] = None
    html_url: str
    default_branch: str = "main"
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    is_private: bool = False
    topics: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GitHubRepoSelectRequest(BaseModel):
    """Payload for selecting a repository as project evidence."""
    repo_full_name: str


class GitHubRepoEvidenceResponse(EvidenceResponse):
    """Response returned when a repository is stored as project evidence."""
    pass
