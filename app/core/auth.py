import httpx
import jwt
import secrets
import time
from pathlib import Path
import base64
from typing import Any, Dict, Optional, Tuple
import logging

from app.config import settings
from app.schemas.auth import SessionData
from app.core.session import (
    create_session,
    delete_session,
    find_session_by_username,
    get_session,
)
from app.db.users import create_user
from app.exceptions import AuthException

logger = logging.getLogger(__name__)


def get_github_app_install_url() -> str:
    """Get the URL for installing the GitHub App."""
    return settings.GITHUB_APP_INSTALLATION_URL


def generate_github_app_jwt() -> str:
    """Generate a JWT for GitHub App authentication."""
    import datetime

    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    payload = {
        "iat": now,
        "exp": now + (5 * 60),
        "iss": settings.GITHUB_APP_ID,
    }

    private_key_b64 = settings.GITHUB_APP_PRIVATE_KEY

    if not private_key_b64:
        raise ValueError("Private key base64 is missing")

    try:
        private_key_bytes = base64.b64decode(private_key_b64)
        private_key = private_key_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decode PEM base64: {str(e)}")
    try:
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT encoding error: {str(e)}")
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
            return None

        return response.json()


async def create_user_session(
    username: str, access_token: str, installation_id: Optional[int] = None
) -> Tuple[str, SessionData]:
    """Create a session for the user, replacing any existing session."""
    await create_user(username=username, installation_id=installation_id)

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


async def refresh_installation_token(installation_id: int) -> str:
    """Refresh the installation token for a GitHub App installation."""
    return await get_installation_access_token(installation_id)


# OAuth Helper Functions
async def get_oauth_access_token(code: str) -> Dict[str, Any]:
    """Exchange OAuth code for access token."""
    url = "https://github.com/login/oauth/access_token"
    
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
        if response.status_code != 200:
            raise AuthException(
                status_code=response.status_code,
                detail=f"Failed to get OAuth access token: {response.text}",
            )
        
        token_data = response.json()
        if "error" in token_data:
            raise AuthException(
                status_code=400,
                detail=f"OAuth error: {token_data.get('error_description', token_data['error'])}",
            )
        
        return token_data


async def get_github_user_oauth(access_token: str) -> Dict[str, Any]:
    """Get GitHub user info using OAuth access token."""
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/user", headers=headers)
        if response.status_code != 200:
            raise AuthException(
                status_code=response.status_code,
                detail=f"Failed to get GitHub user: {response.text}",
            )
        
        return response.json()


def create_jwt_token(username: str, installation_id: Optional[int] = None) -> str:
    """Create a JWT token for the user."""
    from datetime import datetime, timedelta
    
    payload = {
        "sub": username,
        "installation_id": installation_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
