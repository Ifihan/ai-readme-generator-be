from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional


class APIException(Exception):
    """Base class for API exceptions."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


class GitHubException(APIException):
    """Exception raised for errors in the GitHub API."""

    pass


class AIGenerationException(APIException):
    """Exception raised for errors in the AI generation."""

    pass


class ReadmeGenerationException(APIException):
    """Exception raised for errors in README generation."""

    pass


class GeminiApiException(APIException):
    """Exception raised for errors with the Gemini API."""

    pass


class AuthException(APIException):
    """Exception raised for errors in the authentication."""

    pass


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the FastAPI application."""

    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request, exc: APIException
    ) -> JSONResponse:
        """Handle API exceptions."""
        headers = exc.headers or {}
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )

    @app.exception_handler(GitHubException)
    async def github_exception_handler(
        request: Request, exc: GitHubException
    ) -> JSONResponse:
        """Handle GitHub exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": f"GitHub API error: {exc.detail}"},
            headers=exc.headers or {},
        )

    @app.exception_handler(AIGenerationException)
    async def ai_generation_exception_handler(
        request: Request, exc: AIGenerationException
    ) -> JSONResponse:
        """Handle AI generation exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": f"AI generation error: {exc.detail}"},
            headers=exc.headers or {},
        )

    @app.exception_handler(AuthException)
    async def auth_exception_handler(
        request: Request, exc: AuthException
    ) -> JSONResponse:
        """Handle authentication exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": f"Authentication error: {exc.detail}"},
            headers=exc.headers or {},
        )
