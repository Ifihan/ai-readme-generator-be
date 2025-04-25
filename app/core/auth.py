import httpx
import jwt
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from app.config import settings
from app.schemas.auth import SessionData
from app.core.session import (
    create_session,
    delete_session,
    find_session_by_username,
    get_session,
)
from app.exceptions import AuthException


def get_github_app_install_url() -> str:
    """Get the URL for installing the GitHub App."""
    return settings.GITHUB_APP_INSTALLATION_URL


# def generate_github_app_jwt() -> str:
#     """Generate a JWT for GitHub App authentication."""
#     now = int(time.time())
#     payload = {
#         "iat": now,  # Issued at time
#         "exp": now + (10 * 60),  # JWT expires in 10 minutes
#         "iss": settings.GITHUB_APP_ID,
#     }

#     # Use the private key from settings
#     private_key = settings.GITHUB_APP_PRIVATE_KEY_VALUE.replace("\\n", "\n").encode(
#         "utf-8"
#     )

#     # Sign the JWT with the private key
#     encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

#     return encoded_jwt


def generate_github_app_jwt() -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now,  # Issued at time
        "exp": now + (10 * 60),  # JWT expires in 10 minutes
        "iss": settings.GITHUB_APP_ID,
    }

    private_key = settings.GITHUB_APP_PRIVATE_KEY_VALUE
    if "-----BEGIN RSA PRIVATE KEY-----" not in private_key:
        private_key = private_key.replace("\\n", "\n")

    try:
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        return encoded_jwt
    except Exception as e:
        print(f"JWT encoding error: {str(e)}")
        if not private_key.startswith("-----BEGIN"):
            print("Warning: Private key does not appear to have proper PEM headers")
        raise


async def get_installation_access_token(installation_id: int) -> str:
    """Get an installation access token for a specific GitHub App installation."""
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


async def get_installation_info(installation_id: int) -> Dict[str, Any]:
    """Get information about a GitHub App installation."""
    jwt_token = generate_github_app_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise AuthException(
                status_code=response.status_code,
                detail=f"Failed to get installation info: {response.text}",
            )

        return response.json()


async def get_user_from_token(access_token: str) -> Dict[str, Any]:
    """Get user information using an access token."""
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/user", headers=headers)
        if response.status_code != 200:
            # If we can't get user data, we'll rely on installation data
            return None

        return response.json()


async def create_user_session(
    username: str, access_token: str, installation_id: Optional[int] = None
) -> Tuple[str, SessionData]:
    """Create a session for the user, replacing any existing session."""
    existing_session_id = await find_session_by_username(username)
    if existing_session_id:
        await delete_session(existing_session_id)

    # Create a new session
    session_id = secrets.token_urlsafe(32)
    await create_session(
        username=username,
        access_token=access_token,
        session_id=session_id,
        installation_id=installation_id,
    )

    session_data = await get_session(session_id)
    return session_id, session_data


async def refresh_installation_token(installation_id: int) -> str:
    """Refresh the installation token for a GitHub App installation."""
    return await get_installation_access_token(installation_id)
