from typing import Tuple, Optional
import httpx
import logging
from fastapi import HTTPException, status

from app.core.auth import get_installation_access_token, generate_github_app_jwt

# Create a logger for this module
logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """Parse a GitHub repository URL to extract owner and repo name.

    Args:
        repo_url: GitHub repository URL or owner/repo string

    Returns:
        Tuple of (owner, repo)

    Raises:
        HTTPException: If URL format is invalid
    """
    # Handle different URL formats
    if "/" in repo_url:
        # Remove any prefixes like https://github.com/
        parts = repo_url.split("/")
        # Find the owner and repo parts
        if "github.com" in repo_url:
            # Find the position after github.com in the URL
            for i, part in enumerate(parts):
                if part == "github.com" or part.endswith("github.com"):
                    if i + 2 < len(parts):
                        return parts[i + 1], parts[i + 2].split(".git")[0]

        # If we're just given owner/repo format
        if len(parts) >= 2:
            # Take the last two parts
            return parts[-2], parts[-1].split(".git")[0]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid repository URL format. Please use 'owner/repo' or a full GitHub URL.",
    )


async def check_installation_repo_access(
    access_token: str, owner: str, repo: str
) -> bool:
    """
    Check if the token has access to the specified repository.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name

    Returns:
        True if the token has access, False otherwise
    """
    try:
        # Check if we can access this specific repository
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # First, verify the token is valid
        async with httpx.AsyncClient() as client:
            verify_response = await client.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10.0,
            )

            if verify_response.status_code != 200:
                logger.error(
                    f"GitHub token validation failed: {verify_response.status_code}"
                )
                return False

            # Log who we're authenticated as
            user_data = verify_response.json()
            logger.info(f"Token authenticated as user: {user_data.get('login')}")

        # Try to get the repository directly with detailed permissions
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
                timeout=10.0,
            )

            # If we can access the repo directly, check the permissions
            if response.status_code == 200:
                repo_data = response.json()
                # Check if we have admin or write permissions
                permissions = repo_data.get("permissions", {})
                has_write = permissions.get("push", False)
                has_admin = permissions.get("admin", False)

                logger.info(
                    f"Direct repo access: {owner}/{repo} (write: {has_write}, admin: {has_admin})"
                )

                # For README generation, we need at least write access
                return has_write or has_admin

            # If direct access failed, log the specific error
            logger.warning(
                f"Direct repo access failed: {response.status_code}, {response.text}"
            )

            # Check the list of repositories for this installation
            install_response = await client.get(
                "https://api.github.com/installation/repositories",
                headers=headers,
                timeout=10.0,
            )

            if install_response.status_code == 200:
                data = install_response.json()
                # Check if the repository is in the list and has sufficient permissions
                repo_full_name = f"{owner}/{repo}"
                for repository in data.get("repositories", []):
                    if repository.get("full_name") == repo_full_name:
                        permissions = repository.get("permissions", {})
                        has_write = permissions.get("push", False)
                        has_admin = permissions.get("admin", False)

                        logger.info(
                            f"Installation repo access: {repo_full_name} (write: {has_write}, admin: {has_admin})"
                        )

                        # For README generation, we need at least write access
                        return has_write or has_admin

                logger.warning(
                    f"Repository {repo_full_name} not found in installation repositories list"
                )
            else:
                logger.warning(
                    f"Installation repositories check failed: {install_response.status_code}, {install_response.text}"
                )

        logger.warning(f"No access to repository {owner}/{repo} with provided token")
        return False
    except Exception as e:
        # Log the detailed error
        logger.error(
            f"Error checking repository access for {owner}/{repo}: {str(e)}",
            exc_info=True,
        )
        return False


async def get_authenticated_user(access_token: str) -> Optional[str]:
    """
    Get the authenticated user for a token.

    Args:
        access_token: GitHub access token

    Returns:
        Username if successful, None otherwise
    """
    try:
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("login")

        return None
    except Exception as e:
        logger.error(f"Error getting authenticated user: {str(e)}")
        return None


async def validate_repository_access(
    github_service, repository_url: str
) -> Tuple[str, str]:
    """
    Validate that the user has access to the repository through the GitHub service.

    Args:
        github_service: Initialized GitHubService instance with auth token
        repository_url: The repository URL or owner/repo string

    Returns:
        Tuple of (owner, repo)

    Raises:
        HTTPException: If the user doesn't have access to the repository
    """
    # Extract owner and repo from the URL
    owner, repo = parse_repo_url(repository_url)

    # Get access token from service
    if not hasattr(github_service, "access_token") or not github_service.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token available. Please login again.",
        )

    # Get the authenticated user
    username = await get_authenticated_user(github_service.access_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired GitHub token. Please login again.",
        )

    logger.info(f"Validating access to {owner}/{repo} for user {username}")

    # First, check if the repo belongs to the authenticated user
    if username and owner.lower() == username.lower():
        logger.info(
            f"Repository {owner}/{repo} belongs to authenticated user {username}"
        )
        return owner, repo

    # Check if we can access the repository with appropriate permissions
    has_access = await check_installation_repo_access(
        github_service.access_token, owner, repo
    )
    if not has_access:
        # No access - raise 403 error
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have sufficient permissions for {owner}/{repo}. Please ensure the GitHub App is installed on this repository and has write access.",
        )

    logger.info(f"Access verified for repository {owner}/{repo}")
    return owner, repo
