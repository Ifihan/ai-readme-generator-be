from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from app.schemas.auth import SessionData
from app.config import settings

# TODO: use redis or another persistent storage for session data
sessions: Dict[str, SessionData] = {}


async def get_session(session_id: str) -> Optional[SessionData]:
    """Get session by session ID."""
    return sessions.get(session_id)


async def create_session(username: str, access_token: str, session_id: str) -> None:
    """Creates a new session."""
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    session_data = SessionData(
        username=username,
        access_token=access_token,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
    )

    sessions[session_id] = session_data


async def delete_session(session_id: str) -> None:
    """Deletes a session."""
    if session_id in sessions:
        del sessions[session_id]


async def cleanup_expired_sessions() -> None:
    """Cleanup expired sessions."""
    now = datetime.utcnow()

    expired_sessions = [
        session_id for session_id, data in sessions.items() if data.expires_at < now
    ]

    for session_id in expired_sessions:
        await delete_session(session_id)

    return len(expired_sessions)


def validate_session(session_data: SessionData) -> bool:
    """Check if the session is valid."""
    return not session_data.is_expired


async def refresh_session(session_id: str) -> None:
    """Refresh the session expiration time."""
    session_data = await get_session(session_id)
    if not session_data:
        return False

    if session_data.is_expired:
        return False

    new_expires = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    session_data.expires_at = new_expires
    sessions[session_id] = session_data

    return True


async def find_session_by_username(username: str) -> Optional[str]:
    """Find a session by username."""
    for session_id, session_data in sessions.items():
        if session_data.username == username and not session_data.is_expired:
            return session_id
        return None
