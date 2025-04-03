import httpx
import secrets
from typing import Any, Dict, Optional, Tuple

from app.config import settings
from app.schemas.auth import SessionData
from app.core.session import create_session, delete_session, find_session_by_username
from app.core.security import generate_oauth_state, is_valid_github_token_format
from app.exceptions import AuthException


def get_github_auth_url(state: Optional[str] = None) -> str:
    """Generate the GitHub OAuth URL."""
    if state is None:
        state = generate_oauth_state()

    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=public_repo user"  # Scopes: public repo access and user info
        f"&state={state}"
    )


async def exchange_code_for_token(
    code: str, state: Optional[str] = None
) -> Dict[str, Any]:
    """Exchange the GitHub OAuth code for an access token."""
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }

    if state:
        data["state"] = state
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise AuthException(
                status_code=e.response.status_code,
                detail=f"GitHub token exchanged failed: {e.response.text}",
            )
        except Exception as e:
            raise AuthException(
                status_code=500,
                detail=f"Toekn exchange failed: {str(e)}",
            )


async def get_github_user(access_token: str) -> Dict[str, Any]:
    """Get the GitHub user information."""
    if not is_valid_github_token_format(access_token):
        raise AuthException(
            status_code=400,
            detail="Invalid GitHub access token format.",
        )

    # Properly indented code that will execute when the token format is valid
    github_api_url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(github_api_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise AuthException(
                status_code=e.response.status_code,
                detail=f"GitHub user retrieval failed: {e.response.text}",
            )
        except Exception as e:
            raise AuthException(
                status_code=500,
                detail=f"GitHub user retrieval failed: {str(e)}",
            )


async def create_user_session(
    username: str, access_token: str
) -> Tuple[str, Dict[str, SessionData]]:
    """Create a session for the user."""
    existing_session_id = await find_session_by_username(username)
    if existing_session_id:  # Changed from existing_session
        await delete_session(existing_session_id)

    session_id = secrets.token_urlsafe(32)
    await create_session(username, access_token, session_id)

    return session_id, SessionData(
        username=username,
        access_token=access_token,
    )


async def verify_github_token(access_token: str) -> bool:
    """Verify the validity of the GitHub access token."""
    if not is_valid_github_token_format(access_token):
        return False

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://api.github.com/user", headers=headers)
            return response.status_code == 200
        except:
            return False
