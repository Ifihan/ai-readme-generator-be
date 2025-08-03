from fastapi import Depends, Header, HTTPException, status
import jwt
from typing import Dict, Any

from app.config import settings
from app.core.auth import get_installation_access_token
from app.db.users import get_user_by_username
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService


async def verify_auth_header(authorization: str = Header(...)) -> Dict[str, Any]:
    """Verify authorization header and return token payload."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer {token}'",
        )

    token = authorization.split(" ")[1]
    
    print(f"DEBUG: Received token: {token[:50]}...")
    print(f"DEBUG: Using SECRET_KEY: {settings.SECRET_KEY[:10]}...")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(f"DEBUG: Token decoded successfully. Payload keys: {list(payload.keys())}")
        return payload
    except jwt.PyJWTError as e:
        print(f"DEBUG: JWT decode failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT decode failed: {str(e)}. Please get a new token by logging in again.",
        )


async def get_current_user(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> str:
    """Get current user from token payload."""
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return payload["sub"]


async def get_db_user(
    payload: Dict[str, Any] = Depends(verify_auth_header),
):
    """Get current user from database."""
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database",
        )

    return user


async def get_installation_id(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> int:
    """Get GitHub App installation ID from token payload."""
    installation_id = payload.get("installation_id")
    if not installation_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No GitHub installation found. Please install the app first.",
        )
    return installation_id


async def get_github_service(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> GitHubService:
    """Get GitHub service with access token from token payload."""

    installation_id = payload.get("installation_id")
    print(f"DEBUG: installation_id from token: {installation_id}")
    
    if not installation_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No GitHub installation found in token. Token payload: {list(payload.keys())}. Please complete the GitHub App installation.",
        )

    try:
        print(f"DEBUG: Attempting to get access token for installation {installation_id}")
        access_token = await get_installation_access_token(installation_id)
        print(f"DEBUG: Successfully got access token: {access_token[:10]}...")
        return GitHubService(access_token)
    except Exception as e:
        print(f"DEBUG: Failed to get GitHub access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to get GitHub access token for installation {installation_id}: {str(e)}. Please login again.",
        )


def get_gemini_service() -> GeminiService:
    """Get Gemini service instance."""
    return GeminiService()
