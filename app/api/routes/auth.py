import httpx
import jwt
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    Query,
    Header,
)
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from app.core.auth import (
    get_github_app_install_url,
    get_installation_access_token,
    generate_github_app_jwt,
    create_user_session,
    delete_session,
)
from app.core.session import get_session
from app.db.users import get_user_by_username, create_user
from app.config import settings
from app.exceptions import AuthException

router = APIRouter(prefix="/auth")


@router.get("/login", response_model=None)
async def login(
    request: Request,
    authorization: str = Header(None),
) -> Union[JSONResponse, RedirectResponse]:
    """Handle login logic - check if user exists and has valid installation."""

    # If authorization header is provided, check if user is already logged in
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            username = payload["sub"]
            installation_id = payload.get("installation_id")

            # Check if user exists and has valid installation
            user = await get_user_by_username(username)
            if user and installation_id:
                # User is already authenticated with valid installation
                return JSONResponse(
                    {
                        "status": "authenticated",
                        "username": username,
                        "installation_id": installation_id,
                        "token": token,  # Return existing token
                    }
                )
        except (jwt.PyJWTError, Exception):
            # Token is invalid or expired, continue to installation flow
            pass

    # Check if a GitHub user parameter is provided for checking existing users
    github_username = request.query_params.get("username")
    if github_username:
        user = await get_user_by_username(github_username)
        if user and user.installation_id:
            # User exists with installation, check if token is still valid
            try:
                # Try to use the existing installation
                install_token = await get_installation_access_token(
                    user.installation_id
                )

                # Create new session for existing user
                session_id, session_data = await create_user_session(
                    username=github_username,
                    access_token=install_token,
                    installation_id=user.installation_id,
                )

                # Generate JWT token
                payload = {
                    "sub": github_username,
                    "installation_id": user.installation_id,
                    "exp": datetime.utcnow()
                    + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                    "iat": datetime.utcnow(),
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

                return JSONResponse(
                    {
                        "status": "login_successful",
                        "token": token,
                        "username": github_username,
                        "installation_id": user.installation_id,
                    }
                )
            except Exception:
                # Installation token is invalid, need to reinstall
                pass

    # No valid authentication found, provide install URL
    install_url = get_github_app_install_url()
    return JSONResponse(
        {
            "status": "needs_installation",
            "install_url": install_url,
            "message": "Please install the GitHub App to continue",
        }
    )


@router.get("/callback")
async def app_callback(
    installation_id: Optional[int] = Query(None),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    setup_action: Optional[str] = Query(None),
) -> RedirectResponse:
    """Handle the callback after GitHub App installation.

    This endpoint processes GitHub App installation callback with installation_id,
    then redirects to the frontend with a JWT token instead of using cookies.
    """
    try:
        # Check if this is a GitHub App installation callback
        if installation_id:
            # Get installation token
            access_token = await get_installation_access_token(installation_id)

            # Get installation and user data
            async with httpx.AsyncClient() as client:
                # Get installation data
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

                # Attempt to get more user data if possible
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )

                user_data = {"login": username}
                if user_response.status_code == 200:
                    user_data = user_response.json()

            # Create or update user in database
            await create_user(
                username=user_data["login"], installation_id=installation_id
            )

            # Create user session
            session_id, session_data = await create_user_session(
                username=user_data["login"],
                access_token=access_token,
                installation_id=installation_id,
            )

            # Generate JWT token for frontend
            payload = {
                "sub": user_data["login"],
                "installation_id": installation_id,
                "exp": datetime.utcnow()
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

            # Redirect to frontend with token
            redirect_url = f"{settings.REDIRECT_URL}?token={token}"
            return RedirectResponse(url=redirect_url)

        return RedirectResponse(url=f"{settings.API_V1_STR}/auth/login")

    except Exception as e:
        if isinstance(e, AuthException):
            raise e
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub App installation failed: {str(e)}",
        )


@router.post("/verify-token")
async def verify_token(token: str):
    """Verify a JWT token and return user information."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return {
            "valid": True,
            "username": payload["sub"],
            "installation_id": payload.get("installation_id"),
        }
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}"
        )


@router.get("/repositories")
async def get_repositories(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Get repositories for the current user using token-based authentication."""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use 'Bearer {token}'",
            )

        token = authorization.split(" ")[1]

        # Verify the token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            username = payload["sub"]
            installation_id = payload.get("installation_id")
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        if not installation_id:
            return {
                "repositories": [],
                "total_count": 0,
                "message": "No GitHub App installation found. Please install the app first.",
            }

        # Get an installation token for GitHub API access
        token = await get_installation_access_token(installation_id)

        url = "https://api.github.com/installation/repositories"
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
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch repositories: {str(e)}",
        )


@router.get("/me")
async def get_me(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Gets current user information using token-based authentication."""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use 'Bearer {token}'",
            )

        token = authorization.split(" ")[1]

        # Verify the token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            # Get user from database to include any additional info
            user = await get_user_by_username(payload["sub"])

            return {
                "username": payload["sub"],
                "installation_id": payload.get("installation_id"),
                "expires": payload.get("exp"),
                "user_data": user if user else None,
            }
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user information: {str(e)}",
        )


@router.post("/refresh-token")
async def refresh_token(
    authorization: str = Header(...),
) -> Dict[str, str]:
    """Refresh an authentication token."""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use 'Bearer {token}'",
            )

        token = authorization.split(" ")[1]

        # Verify the token
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )

            # Check if token is too old to refresh (e.g., more than 30 days)
            iat = payload.get("iat", 0)
            now = datetime.utcnow().timestamp()
            if iat and (now - iat > 60 * 60 * 24 * 30):  # 30 days
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token too old to refresh, please login again",
                )

            # Create new token
            new_payload = {
                "sub": payload["sub"],
                "installation_id": payload.get("installation_id"),
                "exp": datetime.utcnow()
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.utcnow(),
            }

            new_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm="HS256")

            return {"token": new_token}
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}",
        )


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """Logout endpoint for token-based authentication."""
    return {"message": "Logged out successfully. Please discard your token."}
