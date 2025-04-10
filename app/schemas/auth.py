from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.config import settings


class SessionData(BaseModel):
    """Session data model."""

    username: str
    access_token: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    installation_id: Optional[int] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.now() > self.expires_at


class GitHubAuthResponse(BaseModel):
    """GitHub OAuth response model."""

    access_token: str
    token_type: str
    scope: str


class GitHubUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    avatar_url: str
    url: str
    name: Optional[str] = None
    email: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
