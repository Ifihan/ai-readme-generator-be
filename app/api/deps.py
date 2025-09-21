from fastapi import Depends, Header, HTTPException, status
import jwt
from typing import Dict, Any
import logging

from app.config import settings
from app.core.auth import get_installation_access_token
from app.db.users import get_user_by_username
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

async def verify_auth_header(authorization: str = Header(...)) -> Dict[str, Any]:
    """Verify authorization header and return token payload."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format. Use 'Bearer {token}'")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"JWT decode failed: {str(e)}. Please get a new token by logging in again.")

async def get_current_user(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> str:
    """Get current user from token payload."""
    if "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return payload["sub"]

async def get_db_user(
    payload: Dict[str, Any] = Depends(verify_auth_header),
):
    """Get current user from database."""
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database")

    return user

async def get_installation_id(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> int:
    """Get GitHub App installation ID from token payload."""
    installation_id = payload.get("installation_id")
    if not installation_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No GitHub installation found. Please install the app first.")
    return installation_id

async def get_github_service(
    payload: Dict[str, Any] = Depends(verify_auth_header),
) -> GitHubService:
    """Get GitHub service with access token from token payload."""

    installation_id = payload.get("installation_id")

    if not installation_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No GitHub installation found in token. Token payload: {list(payload.keys())}. Please complete the GitHub App installation.")

    try:
        access_token = await get_installation_access_token(installation_id)
        return GitHubService(access_token)
    except Exception as e:
        logger.error(f"Failed to get GitHub access token for installation {installation_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Failed to get GitHub access token for installation {installation_id}: {str(e)}. Please login again.")

def get_gemini_service() -> GeminiService:
    """Get Gemini service instance."""
    return GeminiService()


async def get_admin_user(
    user: Dict[str, Any] = Depends(get_db_user),
) -> str:
    """Get current user and verify admin privileges."""
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation"
        )
    return user["username"]
