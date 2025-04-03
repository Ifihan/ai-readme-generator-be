from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Optional
from datetime import datetime

from app.core.auth import (
    get_github_auth_url,
    exchange_code_for_token,
    get_github_user,
    create_user_session,
    delete_session,
)
from app.core.security import generate_oauth_state
from app.core.session import get_session
from app.api.deps import get_current_user
from app.schemas.auth import SessionData
from app.config import settings
from app.exceptions import AuthException

router = APIRouter(prefix="/auth")


@router.get("/login")
async def login(request: Request, response: Response) -> JSONResponse:
    """Initiate the GitHub OAuth login process."""
    state = generate_oauth_state()
    auth_url = get_github_auth_url(state=state)

    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,  # 10 minutes
        path="/",
        secure=True,  # Set to true in production
        samesite="lax",
    )

    return JSONResponse({"auth_url": auth_url})


@router.get("/login/redirect")
async def login_redirect() -> RedirectResponse:
    """Redirect to GitHub login page."""
    auth_url = get_github_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str,
    state: Optional[str] = None,
    response: Response = None,
    request: Request = None,
) -> RedirectResponse:
    """Handle GitHub OAuth callback."""
    oauth_state = request.cookies.get("oauth_state") if request else None

    if state and oauth_state and oauth_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    try:
        token_data = await exchange_code_for_token(code, state)
        if "error" in token_data:
            raise AuthException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth error: {token_data['error_description']}",
            )

        access_token = token_data["access_token"]
        user_data = await get_github_user(access_token)

        session_id, session_data = await create_user_session(
            username=user_data["login"], access_token=access_token
        )

        # TODO: change this redirect_url in prod(or use a config)
        redirect_url = "http://localhost:4200/dashboard"
        response_obj = RedirectResponse(url=redirect_url)

        session_data = await get_session(session_id)
        max_age = int((session_data.expires_at - datetime.utcnow()).total_seconds())

        response_obj.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=max_age,
            path="/",
            secure=False,  # TODO: change this in prod to True
            samesite="lax",
        )

        return response_obj
    except Exception as e:
        if isinstance(e, AuthException):
            raise e
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/logout")
async def logout(
    respone: Response, session_data: SessionData = Depends(get_current_user)
) -> Dict[str, str]:
    """Logout the current user and clears the session."""
    await delete_session(session_data.username)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
    )

    return {"message": "Logged out successfully."}


@router.get("/me")
async def get_me(
    session_data: SessionData = Depends(get_current_user),
) -> Dict[str, str]:
    """Gets current user information."""
    return {"username": session_data.username}


@router.get("/debug-create-session", include_in_schema=False)
async def debug_create_session(response: Response):
    """Create a debug session (development only)."""
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404)

    session_id = secrets.token_urlsafe(32)
    await create_session("debug_user", "fake_token", session_id)

    session_data = await get_session(session_id)
    max_age = int((session_data.expires_at - datetime.utcnow()).total_seconds())

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        max_age=max_age,
        path="/",
    )

    return {"session_id": session_id, "message": "Debug session created"}
