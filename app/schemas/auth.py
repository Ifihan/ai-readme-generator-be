from pydantic import BaseModel, Field
from typing import Optional
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

class GitHubInstallation(BaseModel):
    """GitHub App installation model."""

    id: int
    account_login: str
    repository_selection: str
    app_id: int
    target_type: str

class Repository(BaseModel):
    """Repository model."""

    id: int
    name: str
    full_name: str
    html_url: str
    description: Optional[str] = None
    private: bool = False
