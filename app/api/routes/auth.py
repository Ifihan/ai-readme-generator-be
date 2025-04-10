import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Any, Dict, List, Optional
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
    code: str = Query(...),
    state: Optional[str] = Query(None),
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


@router.get("/app-install")
async def install_github_app() -> Dict[str, str]:
    """Generate a URL for installing the GitHub App."""
    from app.core.auth import get_github_app_install_url

    install_url = get_github_app_install_url()
    return {"install_url": install_url}


@router.get("/app-callback")
async def github_app_callback(
    installation_id: int = Query(...),
    setup_action: str = Query(None),
    response: Response = None,
) -> RedirectResponse:
    """Handle the callback after GitHub App installation."""
    try:
        from app.core.auth import get_installation_access_token, generate_github_app_jwt

        access_token = await get_installation_access_token(installation_id)

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            installation_response = await client.get(
                f"https://api.github.com/app/installations/{installation_id}",
                headers={
                    "Authorization": f"Bearer {generate_github_app_jwt()}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if installation_response.status_code != 200:
                raise AuthException(
                    status_code=installation_response.status_code,
                    detail=f"Failed to get installation info: {installation_response.text}",
                )

            installation_data = installation_response.json()
            username = installation_data["account"]["login"]

            user_response = await client.get(
                "https://api.github.com/user", headers=headers
            )

            if user_response.status_code != 200:
                user_data = {"login": username}
            else:
                user_data = user_response.json()

        session_id, session_data = await create_user_session(
            username=user_data["login"],
            access_token=access_token,
            installation_id=installation_id,
        )

        # TODO:: change this redirect_url in prod(or use a config)
        redirect_url = "http://localhost:4200/dashboard"
        response_obj = RedirectResponse(url=redirect_url)

        max_age = int((session_data.expires_at - datetime.utcnow()).total_seconds())

        response_obj.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=max_age,
            path="/",
            secure=False,  # Change to True in production
            samesite="lax",
        )

        return response_obj
    except Exception as e:
        if isinstance(e, AuthException):
            raise e
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub App installation failed: {str(e)}",
        )


@router.get("/installations/{installation_id}/repositories")
async def get_installation_repositories(
    installation_id: int,
    session_data: SessionData = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get repositories for a specific installation."""
    try:
        from app.core.auth import get_installation_access_token

        token = await get_installation_access_token(installation_id)

        url = f"https://api.github.com/installation/repositories"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise AuthException(
                    status_code=response.status_code,
                    detail=f"Failed to get repositories: {response.text}",
                )

            data = response.json()

            # Simplify the repository data
            simplified_repos = [
                {
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "html_url": repo["html_url"],
                    "description": repo["description"],
                    "private": repo["private"],
                }
                for repo in data["repositories"]
            ]

            return {
                "repositories": simplified_repos,
                "total_count": data["total_count"],
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch installation repositories: {str(e)}",
        )


@router.get("/installations")
async def get_installations(
    session_data: SessionData = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get all GitHub app installations for the authenticated user."""
    try:
        from app.core.auth import generate_github_app_jwt

        jwt_token = generate_github_app_jwt()

        url = "https://api.github.com/app/installations"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise AuthException(
                    status_code=response.status_code,
                    detail=f"Failed to get installations: {response.text}",
                )

            installations = response.json()

            # Filter installations to only show those for the current user
            user_installations = [
                installation
                for installation in installations
                if installation["account"]["login"] == session_data.username
            ]

            return user_installations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GitHub app installations: {str(e)}",
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
