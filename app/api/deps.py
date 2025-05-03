# from fastapi import Depends, Header, HTTPException, status
# import jwt
# from typing import Dict, Any

# from app.config import settings
# from app.core.auth import get_installation_access_token
# from app.config import settings
# from app.services.github_service import GitHubService
# from app.services.gemini_service import GeminiService


# async def verify_auth_header(authorization: str = Header(...)) -> Dict[str, Any]:
#     """Verify authorization header and return token payload."""
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authorization header format. Use 'Bearer {token}'",
#         )

#     token = authorization.split(" ")[1]

#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#         return payload
#     except jwt.PyJWTError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Invalid token: {str(e)}",
#         )


# async def get_current_user(
#     payload: Dict[str, Any] = Depends(verify_auth_header),
# ) -> str:
#     """Get current user from token payload."""
#     if "sub" not in payload:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload",
#         )
#     return payload["sub"]


# async def get_installation_id(
#     payload: Dict[str, Any] = Depends(verify_auth_header),
# ) -> int:
#     """Get GitHub App installation ID from token payload."""
#     installation_id = payload.get("installation_id")
#     if not installation_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="No GitHub installation found. Please install the app first.",
#         )
#     return installation_id


# # async def get_github_service(
# #     payload: Dict[str, Any] = Depends(verify_auth_header),
# # ) -> GitHubService:
# #     """Get GitHub service with access token from token payload."""
# #     installation_id = payload.get("installation_id")
# #     if not installation_id:
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="No GitHub installation found. Please install the app first.",
# #         )

# #     access_token = await get_installation_access_token(installation_id)
# #     return GitHubService(access_token)


# async def get_github_service(
#     payload: Dict[str, Any] = Depends(verify_auth_header),
# ) -> GitHubService:
#     """Get GitHub service with access token from token payload."""

#     # Check for test/development environment
#     if settings.ENVIRONMENT == "development":
#         # Use a dummy token for development
#         test_token = settings.GITHUB_TEST_TOKEN
#         return GitHubService(test_token)

#     installation_id = payload.get("installation_id")
#     if not installation_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="No GitHub installation found. Please install the app first.",
#         )

#     access_token = await get_installation_access_token(installation_id)
#     return GitHubService(access_token)


# def get_gemini_service() -> GeminiService:
#     """Get Gemini service instance."""
#     return GeminiService()


from fastapi import Depends, Header, HTTPException, status
import jwt
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth import get_installation_access_token
from app.config import settings
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.db.base import get_db
from app.db import get_user_by_username


async def verify_auth_header(authorization: str = Header(...)) -> Dict[str, Any]:
    """Verify authorization header and return token payload."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer {token}'",
        )

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
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
    db: Session = Depends(get_db),
):
    """Get current user from database."""
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = get_user_by_username(db, username)
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

    # Check for test/development environment
    if settings.ENVIRONMENT == "development":
        # Use a dummy token for development
        test_token = settings.GITHUB_TEST_TOKEN
        return GitHubService(test_token)

    installation_id = payload.get("installation_id")
    if not installation_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No GitHub installation found. Please install the app first.",
        )

    access_token = await get_installation_access_token(installation_id)
    return GitHubService(access_token)


def get_gemini_service() -> GeminiService:
    """Get Gemini service instance."""
    return GeminiService()
