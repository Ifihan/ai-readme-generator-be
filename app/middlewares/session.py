import asyncio
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional

from app.core.session import cleanup_expired_sessions, refresh_session
from app.config import settings


class SessionMiddleWare(BaseHTTPMiddleware):
    """Middleware to handle session management."""

    def __init__(
        self,
        app,
        session_cookie_name: str = settings.SESSION_COOKIE_NAME,
    ):
        super().__init__(app)
        self.session_cookie_name = session_cookie_name
        self.last_cleanup = time.time()
        self.cleanup_interval = 60 * 15  # 15 minutes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """DProcess request and refresh session if needed."""
        session_id = request.cookies.get(self.session_cookie_name)
        respone = await call_next(request)

        if session_id:
            refreshed = await refresh_session(session_id)
            if refreshed:
                from app.core.session import get_session
                from datetime import datetime

                session_data = await get_session(session_id)
                max_age = (session_data.expires_at - datetime.utcnow()).total_seconds()
                respone.set_cookie(
                    key=self.session_cookie_name,
                    value=session_id,
                    httponly=True,
                    max_age=max_age,
                    path="/",
                    secure=True,  # TODO: set to True in production
                    samesite="lax",
                )
        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            asyncio.create_task(cleanup_expired_sessions())
            self.last_cleanup = current_time

        return respone  # Add this line

    async def _cleanup_sessions(self):
        """Cleanup expired sessions in the background."""
        try:
            removed = await cleanup_expired_sessions()
            print(f"Session cleanup: removed {removed} expired sessions")
        except Exception as e:
            print(f"Error during session cleanup: {str(e)}")
