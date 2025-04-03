from fastapi import Depends, HTTPException, status, Cookie
from typing import Optional
from app.core.session import get_session, validate_session
from app.schemas.auth import SessionData


async def get_current_user(
    session_id: Optional[str] = Cookie(None),
) -> Optional[SessionData]:
    """Get the current user from the session."""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session_data = await get_session(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if session_data.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session_data
