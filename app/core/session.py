# from datetime import datetime, timedelta
# from typing import Dict, Optional

# from app.schemas.auth import SessionData
# from app.config import settings

# sessions: Dict[str, SessionData] = {}  # should use Redis


# async def get_session(session_id: str) -> Optional[SessionData]:
#     """Get session by session ID."""
#     return sessions.get(session_id)


# async def create_session(
#     username: str,
#     access_token: str,
#     session_id: str,
#     installation_id: Optional[int] = None,
# ) -> None:
#     """Creates a new session."""
#     expires_at = datetime.utcnow() + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )

#     session_data = SessionData(
#         username=username,
#         access_token=access_token,
#         created_at=datetime.utcnow(),
#         expires_at=expires_at,
#         installation_id=installation_id,
#     )

#     sessions[session_id] = session_data


# async def delete_session(session_id: str) -> None:
#     """Deletes a session."""
#     if session_id in sessions:
#         del sessions[session_id]


# async def cleanup_expired_sessions() -> int:
#     """Cleanup expired sessions and return the count of removed sessions."""
#     now = datetime.utcnow()

#     expired_sessions = [
#         session_id for session_id, data in sessions.items() if data.is_expired
#     ]

#     for session_id in expired_sessions:
#         await delete_session(session_id)

#     return len(expired_sessions)


# def validate_session(session_data: SessionData) -> bool:
#     """Check if the session is valid."""
#     return not session_data.is_expired


# async def refresh_session(session_id: str) -> bool:
#     """Refresh the session expiration time."""
#     session_data = await get_session(session_id)
#     if not session_data:
#         return False

#     if session_data.is_expired:
#         return False

#     new_expires = datetime.utcnow() + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )
#     session_data.expires_at = new_expires
#     sessions[session_id] = session_data

#     return True


# async def find_session_by_username(username: str) -> Optional[str]:
#     """Find a session by username."""
#     for session_id, session_data in sessions.items():
#         if session_data.username == username and not session_data.is_expired:
#             return session_id
#     return None


import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.config import settings
from app.schemas.auth import SessionData

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL)


async def create_session(
    username: str,
    access_token: str,
    session_id: str,
    installation_id: Optional[int] = None,
) -> str:
    """Create a new session."""
    session_data = SessionData(
        username=username,
        access_token=access_token,
        installation_id=installation_id,
    )

    # Convert session data to JSON and store in Redis
    session_json = session_data.model_dump_json()
    await redis_client.set(
        f"session:{session_id}",
        session_json,
        ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # Create index for reverse lookup (username -> session_id)
    await redis_client.set(f"username:{username}", session_id)

    return session_id


async def get_session(session_id: str) -> Optional[SessionData]:
    """Get session data by session ID."""
    session_json = await redis_client.get(f"session:{session_id}")
    if not session_json:
        return None

    session_data = json.loads(session_json)
    # Convert string dates back to datetime objects
    if "created_at" in session_data:
        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
    if "expires_at" in session_data:
        session_data["expires_at"] = datetime.fromisoformat(session_data["expires_at"])

    return SessionData(**session_data)


async def refresh_session(session_id: str) -> bool:
    """Refresh the session expiration time."""
    session_data = await get_session(session_id)
    if not session_data:
        return False

    if session_data.is_expired:
        await delete_session(session_id)
        return False

    # Update expiration time
    session_data.expires_at = datetime.now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Save updated session data
    session_json = session_data.model_dump_json()
    await redis_client.set(
        f"session:{session_id}",
        session_json,
        ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return True


async def delete_session(session_id: str) -> bool:
    """Delete a session."""
    session_data = await get_session(session_id)
    if not session_data:
        return False

    # Remove username index
    await redis_client.delete(f"username:{session_data.username}")

    # Remove session data
    await redis_client.delete(f"session:{session_id}")
    return True


async def find_session_by_username(username: str) -> Optional[str]:
    """Find session ID by username."""
    session_id = await redis_client.get(f"username:{username}")
    if not session_id:
        return None
    return session_id.decode("utf-8")


async def cleanup_expired_sessions() -> int:
    """Clean up expired sessions. Returns number of deleted sessions."""
    # This is a simplified approach. In production, you might want a more efficient solution.
    pattern = "session:*"
    cursor = 0
    deleted_count = 0

    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)

        for key in keys:
            session_id = key.decode("utf-8").split(":", 1)[1]
            session_data = await get_session(session_id)

            if not session_data or session_data.is_expired:
                if await delete_session(session_id):
                    deleted_count += 1

        if cursor == 0:
            break

    return deleted_count
