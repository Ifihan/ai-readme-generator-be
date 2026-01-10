from typing import Tuple, Optional
from urllib.parse import urlparse
import httpx
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """Parse a GitHub repository URL to extract owner and repo name."""
    # Handle simple owner/repo format
    if "/" in repo_url and not repo_url.startswith(("http://", "https://")):
        parts = repo_url.split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1].split(".git")[0]

    # Handle full URLs - use proper URL parsing
    if repo_url.startswith(("http://", "https://")):
        try:
            parsed = urlparse(repo_url)
            # Validate that it's actually github.com domain
            if parsed.netloc not in ["github.com", "www.github.com"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only GitHub repository URLs are supported."
                )

            # Extract owner and repo from path
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].split(".git")[0]
                return owner, repo
        except Exception as e:
            logger.error(f"Error parsing repository URL: {str(e)}")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid repository URL format. Please use 'owner/repo' or a full GitHub URL."
    )

async def check_installation_repo_access(
    access_token: str, owner: str, repo: str
) -> bool:
    """Check if the token has access to the specified repository."""
    try:
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:

            all_repositories = []
            page = 1
            per_page = 100

            while True:
                install_response = await client.get(
                    f"https://api.github.com/installation/repositories?per_page={per_page}&page={page}",
                    headers=headers,
                    timeout=10.0,
                )

                if install_response.status_code != 200:
                    logger.warning(f"Failed to get installation repos (page {page}): {install_response.status_code}")
                    break

                data = install_response.json()
                repositories = data.get("repositories", [])

                if not repositories:
                    break

                all_repositories.extend(repositories)
                page += 1

                if len(repositories) < per_page:
                    break

            repo_full_name = f"{owner}/{repo}"
            for repository in all_repositories:
                if repository.get("full_name") == repo_full_name:
                    logger.info(f"Installation repo access confirmed for: {repo_full_name}")
                    return True

            logger.warning(f"Repository {repo_full_name} not found in installation repositories list")

        logger.warning(f"No access to repository {owner}/{repo} with provided token")
        return False
    except Exception as e:
        logger.error(f"Error checking repository access for {owner}/{repo}: {str(e)}", exc_info=True)
        return False

async def get_authenticated_user(access_token: str) -> Optional[str]:
    """Get the authenticated user for a token."""
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
                username = data.get("login")
                return username

        return None
    except Exception as e:
        logger.error(f"Error getting authenticated user: {str(e)}")
        return None

async def validate_repository_access(
    github_service, repository_url: str
) -> Tuple[str, str]:
    """Validate that the user has access to the repository through the GitHub service."""
    owner, repo = parse_repo_url(repository_url)

    if not hasattr(github_service, "access_token") or not github_service.access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No authentication token available. Please login again.")

    logger.info(f"Validating access to {owner}/{repo} using installation token")

    has_access = await check_installation_repo_access(github_service.access_token, owner, repo)
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have sufficient permissions for {owner}/{repo}. Please ensure the GitHub App is installed on this repository and has write access.")

    logger.info(f"Access verified for repository {owner}/{repo}")
    return owner, repo
