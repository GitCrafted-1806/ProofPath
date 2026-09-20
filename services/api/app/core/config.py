from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to ProofPath repository root
APP_DIR = Path(__file__).resolve().parent.parent
API_DIR = APP_DIR.parent
ROOT_DIR = API_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_PATH = DATA_DIR / "proofpath.db"


class Settings(BaseSettings):
    DEMO_MODE: bool = True
    DATABASE_URL: str = f"sqlite:///{DEFAULT_SQLITE_PATH}"
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

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=[
            str(API_DIR / ".env"),
            str(ROOT_DIR / ".env")
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
