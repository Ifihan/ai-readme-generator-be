from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI README Generator"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "https://ai-readme-generator-be-912048666815.us-central1.run.app",
        "0.0.0.0",
    ]
    ENVIRONMENT: str = "development"  # Options: development, production, testing

    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_COOKIE_NAME: str = "readme_generator_session"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # GitHub App settings
    GITHUB_APP_ID: str
    GITHUB_APP_PRIVATE_KEY: str
    GITHUB_APP_INSTALLATION_URL: str
    GITHUB_TEST_TOKEN: Optional[str]

    REDIRECT_URL: str

    GEMINI_API_KEY: str
    GEMINI_MODEL: str

    # MongoDB settings
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
