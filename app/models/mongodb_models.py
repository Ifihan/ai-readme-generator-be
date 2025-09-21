from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class PyObjectId(str):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        from bson.objectid import ObjectId

        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserModel(BaseModel):
    """User model for MongoDB."""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    installation_id: Optional[int] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    github_id: Optional[int] = None
    public_repos: Optional[int] = None
    company: Optional[str] = None
    is_admin: bool = Field(default=False, description="Whether user has admin privileges")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            PyObjectId: lambda oid: str(oid),
        }

class SessionModel(BaseModel):
    """Session model for MongoDB."""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    session_id: str
    username: str
    access_token: str
    installation_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            PyObjectId: lambda oid: str(oid),
        }

def user_helper(user) -> Dict[str, Any]:
    """Helper function to convert MongoDB user to dict."""
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "installation_id": user.get("installation_id"),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "avatar_url": user.get("avatar_url"),
        "github_id": user.get("github_id"),
        "public_repos": user.get("public_repos"),
        "company": user.get("company"),
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"],
        "last_login": user["last_login"],
    }

def session_helper(session) -> Dict[str, Any]:
    """Helper function to convert MongoDB session to dict."""
    return {
        "id": str(session["_id"]),
        "session_id": session["session_id"],
        "username": session["username"],
        "access_token": session["access_token"],
        "installation_id": session.get("installation_id"),
        "created_at": session["created_at"],
        "expires_at": session["expires_at"],
    }


class FeedbackModel(BaseModel):
    """Feedback model for MongoDB."""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    readme_history_id: str
    repository_name: str
    rating: str
    helpful_sections: Optional[List[str]] = None
    problematic_sections: Optional[List[str]] = None
    general_comments: Optional[str] = None
    suggestions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            PyObjectId: lambda oid: str(oid),
        }


def feedback_helper(feedback) -> Dict[str, Any]:
    """Helper function to convert MongoDB feedback to dict."""
    return {
        "id": str(feedback["_id"]),
        "username": feedback["username"],
        "readme_history_id": feedback["readme_history_id"],
        "repository_name": feedback["repository_name"],
        "rating": feedback["rating"],
        "helpful_sections": feedback.get("helpful_sections", []),
        "problematic_sections": feedback.get("problematic_sections", []),
        "general_comments": feedback.get("general_comments", ""),
        "suggestions": feedback.get("suggestions", ""),
        "created_at": feedback["created_at"],
    }
