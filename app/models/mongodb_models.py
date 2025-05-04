from datetime import datetime
from typing import Optional, Dict, Any
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
