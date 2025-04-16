import httpx
import jwt
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple, List

from app.config import settings
from app.schemas.auth import SessionData
from app.core.session import (
    create_session,
    delete_session,
    find_session_by_username,
    get_session,
)
from app.core.security import generate_oauth_state, is_valid_github_token_format
from app.exceptions import AuthException


def get_github_auth_url(state: Optional[str] = None) -> str:
    """Generate the GitHub OAuth URL."""
    if state is None:
        state = generate_oauth_state()

    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_OAUTH_ID}"
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
        "client_id": settings.GITHUB_CLIENT_OAUTH_ID,
        "client_secret": settings.GITHUB_CLIENT_OAUTH_SECRET,
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
    username: str, access_token: str, installation_id: Optional[int] = None
) -> Tuple[str, SessionData]:
    """Create a session for the user."""
    existing_session_id = await find_session_by_username(username)
    if existing_session_id:
        await delete_session(existing_session_id)

    session_id = secrets.token_urlsafe(32)
    await create_session(
        username=username,
        access_token=access_token,
        session_id=session_id,
        installation_id=installation_id,
    )

    session_data = await get_session(session_id)
    return session_id, session_data


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


def generate_github_app_jwt() -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now,  # Issued at time
        "exp": now + (10 * 60),  # JWT expires in 10 minutes
        "iss": settings.GITHUB_APP_ID,
    }

    # Read the private key
    # with open(settings.GITHUB_APP_PRIVATE_KEY_PATH, "rb") as key_file:
    #     private_key = key_file.read()

    # key = settings.GITHUB_APP_PRIVATE_KEY_PATH
    # private_key = key.encode("utf-8")
    private_key = settings.GITHUB_APP_PRIVATE_KEY_VALUE.replace("\\n", "\n").encode(
        "utf-8"
    )

    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    return encoded_jwt


async def get_installation_access_token(installation_id: int) -> str:
    """Get an installation access token for a specific installation."""
    jwt_token = generate_github_app_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        if response.status_code != 201:
            raise AuthException(
                status_code=response.status_code,
                detail=f"Failed to get installation token: {response.text}",
            )

        data = response.json()
        return data["token"]


def get_github_app_install_url() -> str:
    """Get the URL for installing the GitHub App."""
    return settings.GITHUB_APP_INSTALLATION_URL
