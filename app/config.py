from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings for the application."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI README Generator"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:4200", "http://localhost:3000"]

    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_COOKIE_NAME: str = "readme_generator_session"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CLIENT_OAUTH_ID: str
    GITHUB_CLIENT_OAUTH_SECRET: str
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    GITHUB_APP_ID: str
    GITHUB_APP_PRIVATE_KEY_VALUE: str
    GITHUB_APP_INSTALLATION_URL: str
    REDIRECT_URL: str

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-pro"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
