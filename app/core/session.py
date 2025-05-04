import time
from datetime import datetime, timedelta
from typing import Optional

from app.db.mongodb import get_database
from app.schemas.auth import SessionData
from app.config import settings


async def create_session(
    username: str,
    access_token: str,
    session_id: str,
    installation_id: Optional[int] = None,
) -> str:
    """Create a new session in MongoDB."""
    db = get_database()
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    session_data = {
        "session_id": session_id,
        "username": username,
        "access_token": access_token,
        "installation_id": installation_id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
    }

    result = await db.sessions.insert_one(session_data)
    return session_id


async def get_session(session_id: str) -> Optional[SessionData]:
    """Get session data from MongoDB."""
    db = get_database()
    session = await db.sessions.find_one({"session_id": session_id})

    if not session:
        return None

    # Convert MongoDB document format to SessionData
    return SessionData(
        username=session["username"],
        access_token=session["access_token"],
        created_at=session["created_at"],
        expires_at=session["expires_at"],
        installation_id=session.get("installation_id"),
    )


async def find_session_by_username(username: str) -> Optional[str]:
    """Find session ID by username."""
    db = get_database()
    session = await db.sessions.find_one({"username": username})

    if session:
        return session["session_id"]
    return None


async def delete_session(session_id: str) -> bool:
    """Delete a session from MongoDB."""
    db = get_database()
    result = await db.sessions.delete_one({"session_id": session_id})
    return result.deleted_count > 0


async def refresh_session(session_id: str) -> bool:
    """Refresh session expiration time."""
    db = get_database()
    session = await db.sessions.find_one({"session_id": session_id})

    if not session:
        return False

    # Check if session is expired
    if session["expires_at"] < datetime.utcnow():
        await delete_session(session_id)
        return False

    # Update expiration time
    new_expires_at = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    result = await db.sessions.update_one(
        {"session_id": session_id}, {"$set": {"expires_at": new_expires_at}}
    )

    return result.modified_count > 0


async def cleanup_expired_sessions() -> int:
    """Remove expired sessions from MongoDB."""
    db = get_database()
    result = await db.sessions.delete_many({"expires_at": {"$lt": datetime.utcnow()}})
    return result.deleted_count
