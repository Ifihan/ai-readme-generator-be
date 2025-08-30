import httpx
import jwt

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Header,
)
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta, timezone

from app.core.auth import (
    get_github_app_install_url,
    get_installation_access_token,
    generate_github_app_jwt,
    create_user_session,
    get_oauth_access_token,
    get_github_user_oauth,
    create_jwt_token,
)
from app.db.users import get_user_by_username, create_user
from app.config import settings
from app.exceptions import AuthException

router = APIRouter(prefix="/auth")


@router.get("/login", response_model=None)
async def login(
    authorization: str = Header(None),
) -> Union[JSONResponse, RedirectResponse]:
    """Handle login logic - start OAuth for user identification, then GitHub App if needed."""

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
                # Verify installation is still valid
                try:
                    await get_installation_access_token(installation_id)
                    # User is already authenticated with valid installation
                    return JSONResponse(
                        {
                            "status": "authenticated",
                            "username": username,
                            "installation_id": installation_id,
                            "token": token,
                        }
                    )
                except Exception:
                    # Installation token invalid, continue to OAuth flow
                    pass
        except (jwt.PyJWTError, Exception):
            # Token is invalid or expired, continue to OAuth flow
            pass

    # For login, always start with OAuth to identify the user
    # This ensures we get proper user data and can determine next steps
    oauth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.OAUTH_REDIRECT_URL}&"
        f"scope=user:email"
    )
    
    return JSONResponse(
        {
            "status": "oauth_redirect",
            "oauth_url": oauth_url,
            "message": "Redirecting to GitHub OAuth for user identification",
        }
    )


@router.get("/callback")
async def app_callback(
    installation_id: Optional[int] = Query(None),
    state: Optional[str] = Query(None),
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

            # Get username from installation data
            username = user_data["login"]

            # Get existing user data if user exists (to preserve OAuth-collected data)
            existing_user = await get_user_by_username(username)
            
            # Merge GitHub data - prioritize OAuth data over installation data
            merged_github_data = user_data.copy()
            if existing_user:
                # If we have OAuth data from earlier, preserve it
                for field in ["email", "name", "avatar_url", "id", "public_repos", "company"]:
                    if existing_user.get(field.replace("name", "full_name") if field == "name" else field):
                        if field == "name":
                            merged_github_data["name"] = existing_user.get("full_name")
                        elif field == "id":
                            merged_github_data["id"] = existing_user.get("github_id")
                        else:
                            merged_github_data[field] = existing_user.get(field)

            # Create or update user in database with installation_id
            await create_user(
                username=username,
                installation_id=installation_id,
                github_data=merged_github_data,
            )

            # Create user session with installation access token
            await create_user_session(
                username=username,
                access_token=access_token,
                installation_id=installation_id,
            )

            # Generate JWT token for frontend
            token = create_jwt_token(username, installation_id)

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")


@router.get("/repositories")
async def get_repositories(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Get repositories for the current user using token-based authentication."""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format. Use 'Bearer {token}'")

        token = authorization.split(" ")[1]

        # Verify the token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            installation_id = payload.get("installation_id")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        if not installation_id:
            return {
                "repositories": [],
                "total_count": 0,
                "message": "No GitHub App installation found. Please install the app first.",
            }

        # Get an installation token for GitHub API access
        token = await get_installation_access_token(installation_id)

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            # Handle pagination to get all repositories
            all_repositories = []
            page = 1
            per_page = 100  # Maximum allowed by GitHub API
            
            while True:
                url = f"https://api.github.com/installation/repositories?per_page={per_page}&page={page}"
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    raise AuthException(status_code=response.status_code, detail=f"Failed to get repositories: {response.text}")

                data = response.json()
                repositories = data.get("repositories", [])
                
                if not repositories:
                    break
                    
                all_repositories.extend(repositories)
                page += 1
                
                if len(repositories) < per_page:
                    break

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
                for repo in all_repositories
            ]

            return {
                "repositories": simplified_repos,
                "total_count": len(all_repositories),
            }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch repositories: {str(e)}")


@router.get("/me")
async def get_me(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Gets current user information using token-based authentication."""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format. Use 'Bearer {token}'")

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format. Use 'Bearer {token}'")

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
            now = datetime.now(timezone.utc).timestamp()
            if iat and (now - iat > 60 * 60 * 24 * 30):  # 30 days
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token too old to refresh, please login again",
                )

            # Create new token
            new_payload = {
                "sub": payload["sub"],
                "installation_id": payload.get("installation_id"),
                "exp": datetime.now(timezone.utc)
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.now(timezone.utc),
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


@router.get("/oauth/login")
async def oauth_login() -> JSONResponse:
    """Initiate GitHub OAuth flow for user identification."""
    oauth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.OAUTH_REDIRECT_URL}&"
        f"scope=user:email"
    )

    return JSONResponse(
        {
            "status": "oauth_redirect",
            "oauth_url": oauth_url,
            "message": "Redirecting to GitHub OAuth",
        }
    )


@router.get("/status/{username}")
async def get_user_status(username: str) -> JSONResponse:
    """Check the onboarding/authentication status of a user."""
    try:
        user = await get_user_by_username(username)
        
        if not user:
            return JSONResponse(
                {
                    "status": "not_found",
                    "message": "User does not exist",
                    "next_step": "signup",
                }
            )
        
        # Check if user has GitHub data
        has_github_data = bool(user.get("email") or user.get("full_name") or user.get("avatar_url"))
        
        if user.get("installation_id"):
            # User has completed onboarding
            try:
                # Verify installation is still valid
                await get_installation_access_token(user["installation_id"])
                return JSONResponse(
                    {
                        "status": "complete",
                        "message": "User fully authenticated",
                        "next_step": "login",
                        "has_github_data": has_github_data,
                    }
                )
            except Exception:
                # Installation invalid, needs reinstall
                return JSONResponse(
                    {
                        "status": "installation_invalid",
                        "message": "GitHub App installation is invalid",
                        "next_step": "github_app_install",
                        "has_github_data": has_github_data,
                    }
                )
        else:
            # User exists but no GitHub App installation
            return JSONResponse(
                {
                    "status": "incomplete",
                    "message": "User needs to install GitHub App",
                    "next_step": "github_app_install",
                    "has_github_data": has_github_data,
                    "install_url": get_github_app_install_url(),
                }
            )
            
    except Exception as e:
        return JSONResponse(
            {
                "status": "error",
                "message": f"Error checking user status: {str(e)}",
                "next_step": "signup",
            },
            status_code=500,
        )


@router.get("/oauth/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
) -> RedirectResponse:
    """Handle GitHub OAuth callback and determine user flow."""
    try:
        if error:
            # OAuth was denied or failed
            redirect_url = f"{settings.REDIRECT_URL}?error={error}"
            return RedirectResponse(url=redirect_url)

        if not code:
            redirect_url = f"{settings.REDIRECT_URL}?error=no_code"
            return RedirectResponse(url=redirect_url)

        # Exchange code for OAuth access token
        token_data = await get_oauth_access_token(code)
        oauth_access_token = token_data["access_token"]

        # Get user info from GitHub
        user_data = await get_github_user_oauth(oauth_access_token)
        username = user_data["login"]

        # Check if user exists in database
        existing_user = await get_user_by_username(username)

        if existing_user and existing_user.get("installation_id"):
            # Existing user with GitHub App installed - verify and login
            try:
                # Verify installation is still valid
                await get_installation_access_token(existing_user["installation_id"])

                # Update user data and last login
                await create_user(
                    username=username,
                    installation_id=existing_user["installation_id"],
                    github_data=user_data,
                )

                # Get installation access token for session
                installation_access_token = await get_installation_access_token(existing_user["installation_id"])
                
                # Create user session with installation access token
                await create_user_session(
                    username=username,
                    access_token=installation_access_token,
                    installation_id=existing_user["installation_id"],
                )

                # Create JWT token
                jwt_token = create_jwt_token(username, existing_user["installation_id"])

                # Redirect to frontend with token (successful login)
                redirect_url = f"{settings.REDIRECT_URL}?token={jwt_token}"
                return RedirectResponse(url=redirect_url)

            except Exception:
                # Installation token invalid, need to reinstall
                # Update user to remove invalid installation_id
                await create_user(
                    username=username, installation_id=None, github_data=user_data
                )

        elif existing_user and not existing_user.get("installation_id"):
            # Existing user with incomplete onboarding - update data and redirect to GitHub App
            await create_user(
                username=username, installation_id=None, github_data=user_data
            )

        else:
            # New user - create with GitHub data but no installation_id
            await create_user(
                username=username, installation_id=None, github_data=user_data
            )

        # New user or user without GitHub App installation
        # Redirect to GitHub App installation
        # Note: GitHub App installations don't support custom state parameters
        # The username will be identified from the installation account info
        install_url = get_github_app_install_url()
        return RedirectResponse(url=install_url)

    except Exception as e:
        if isinstance(e, AuthException):
            raise e
        raise AuthException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}",
        )


@router.post("/test/create-user")
async def create_test_user(
    username: str, installation_id: int = 12345
) -> Dict[str, Any]:
    """Create a test user for development/testing purposes."""
    test_github_data = {
        "login": username,
        "id": 12345,
        "email": f"{username}@example.com",
        "name": f"Test User {username}",
        "avatar_url": f"https://avatars.githubusercontent.com/{username}",
        "public_repos": 10,
        "company": "Test Company",
    }

    user = await create_user(
        username=username, installation_id=installation_id, github_data=test_github_data
    )

    # Generate test JWT token
    payload = {
        "sub": username,
        "installation_id": installation_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return {
        "user": user,
        "token": token,
        "message": f"Test user '{username}' created successfully",
    }


# GitHub App Settings Endpoints
@router.get("/settings/installation")
async def get_installation_settings(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Get GitHub App installation details and settings."""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        installation_id = payload.get("installation_id")

        if not installation_id:
            return {
                "status": "no_installation",
                "message": "No GitHub App installation found",
                "install_url": get_github_app_install_url(),
            }

        # Get installation details from GitHub
        async with httpx.AsyncClient() as client:
            # Get installation info
            installation_response = await client.get(
                f"https://api.github.com/app/installations/{installation_id}",
                headers={
                    "Authorization": f"Bearer {generate_github_app_jwt()}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if installation_response.status_code != 200:
                raise HTTPException(
                    status_code=installation_response.status_code,
                    detail="Failed to get installation details",
                )

            installation_data = installation_response.json()

            # Get installation repositories
            install_token = await get_installation_access_token(installation_id)
            repos_response = await client.get(
                "https://api.github.com/installation/repositories",
                headers={
                    "Authorization": f"token {install_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            repos_data = repos_response.json() if repos_response.status_code == 200 else {"repositories": []}

            return {
                "installation": {
                    "id": installation_data["id"],
                    "account": installation_data["account"]["login"],
                    "app_slug": installation_data["app_slug"],
                    "created_at": installation_data["created_at"],
                    "updated_at": installation_data["updated_at"],
                    "permissions": installation_data["permissions"],
                    "events": installation_data["events"],
                    "repository_selection": installation_data["repository_selection"],
                },
                "repositories": {
                    "total_count": repos_data.get("total_count", 0),
                    "repositories": [
                        {
                            "id": repo["id"],
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "private": repo["private"],
                            "permissions": repo.get("permissions", {}),
                        }
                        for repo in repos_data.get("repositories", [])
                    ],
                },
                "settings_url": f"https://github.com/settings/installations/{installation_id}",
            }

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get installation settings: {str(e)}",
        )


@router.post("/settings/reinstall")
async def reinstall_github_app(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Generate reinstall URL for GitHub App (for changing permissions)."""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

        token = authorization.split(" ")[1]
        jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        install_url = get_github_app_install_url()
        
        return {
            "status": "reinstall_ready",
            "install_url": install_url,
            "message": "Redirect user to this URL to reconfigure GitHub App permissions",
        }

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@router.delete("/settings/revoke")
async def revoke_github_app(
    authorization: str = Header(...),
) -> Dict[str, Any]:
    """Revoke GitHub App installation and clear user data."""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload["sub"]
        installation_id = payload.get("installation_id")

        if not installation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub App installation to revoke",
            )

        # Clear installation_id from user record
        await create_user(username=username, installation_id=None, github_data=None)

        return {
            "status": "revoked",
            "message": "GitHub App access revoked. You'll need to reinstall to continue using the service.",
            "github_revoke_url": f"https://github.com/settings/installations/{installation_id}",
        }

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke GitHub App: {str(e)}",
        )
