from pathlib import Path
from typing import List, Union, Optional
import json
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to ProofPath repository root
APP_DIR = Path(__file__).resolve().parent.parent
API_DIR = APP_DIR.parent
ROOT_DIR = API_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_PATH = DATA_DIR / "proofpath.db"


UPLOAD_DIR_DEFAULT = DATA_DIR / "uploads"
UPLOAD_DIR_DEFAULT.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    DEMO_MODE: bool = True
    DATABASE_URL: str = f"sqlite:///{DEFAULT_SQLITE_PATH}"
    SECRET_KEY: Optional[str] = None
    JWT_SECRET: str = "change-this-in-development-super-secret-key-proofpath"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8081"
    ]
    UPLOAD_DIR: Path = UPLOAD_DIR_DEFAULT
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png"]
    TESSERACT_CMD: Union[str, None] = None

    # GitHub OAuth & API Configuration
    GITHUB_CLIENT_ID: Union[str, None] = None
    GITHUB_CLIENT_SECRET: Union[str, None] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/github/callback"
    GITHUB_OAUTH_AUTHORIZE_URL: str = "https://github.com/login/oauth/authorize"
    GITHUB_OAUTH_TOKEN_URL: str = "https://github.com/login/oauth/access_token"
    GITHUB_API_BASE_URL: str = "https://api.github.com"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Optional[str]) -> str:
        if not v or not str(v).strip():
            return f"sqlite:///{DEFAULT_SQLITE_PATH}"
        cleaned = str(v).strip().strip("'\"")
        # Handle postgres:// scheme (common on Supabase, Heroku, Render) for SQLAlchemy compatibility
        if cleaned.startswith("postgres://"):
            return "postgresql://" + cleaned[len("postgres://"):]
        return cleaned

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            cleaned = v.strip().strip("'\"")
            if cleaned.startswith("[") and cleaned.endswith("]"):
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        return [str(i).strip().strip("'\"") for i in parsed if i]
                except Exception:
                    pass
            origins = [i.strip().strip("'\"") for i in cleaned.split(",") if i.strip().strip("'\"")]
            if origins:
                return origins
        elif isinstance(v, list):
            return [str(i).strip().strip("'\"") for i in v if i]
        return [
            "http://localhost:3000",
            "http://localhost:8081",
            "http://localhost:19006",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8081"
        ]

    @model_validator(mode="after")
    def sync_secrets(self) -> "Settings":
        # Keep SECRET_KEY and JWT_SECRET synchronized
        if self.SECRET_KEY and self.SECRET_KEY.strip():
            self.JWT_SECRET = self.SECRET_KEY.strip()
        else:
            self.SECRET_KEY = self.JWT_SECRET
        return self

    model_config = SettingsConfigDict(
        env_file=[
            str(API_DIR / ".env"),
            str(ROOT_DIR / ".env")
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
