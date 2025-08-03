import asyncio
import time
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from datetime import datetime

from app.core.session import cleanup_expired_sessions, refresh_session, get_session
from app.config import settings

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle session management."""

    def __init__(
        self,
        app,
        session_cookie_name: str = settings.SESSION_COOKIE_NAME,
    ):
        super().__init__(app)
        self.session_cookie_name = session_cookie_name
        self.last_cleanup = time.time()
        self.cleanup_interval = 60 * 15

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and refresh session if needed."""
        session_id = request.cookies.get(self.session_cookie_name)
        response = await call_next(request)

        if session_id:
            refreshed = await refresh_session(session_id)
            if refreshed:
                session_data = await get_session(session_id)
                if session_data:
                    max_age = int(
                        (session_data.expires_at - datetime.utcnow()).total_seconds()
                    )
                    response.set_cookie(
                        key=self.session_cookie_name,
                        value=session_id,
                        httponly=True,
                        max_age=max_age,
                        path="/",
                        secure=settings.ENVIRONMENT == "production",
                        samesite="lax",
                    )

        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            asyncio.create_task(self._cleanup_sessions())
            self.last_cleanup = current_time

        return response

    async def _cleanup_sessions(self):
        """Cleanup expired sessions in the background."""
        try:
            removed = await cleanup_expired_sessions()
            logger.info(f"Session cleanup: removed {removed} expired sessions")
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
