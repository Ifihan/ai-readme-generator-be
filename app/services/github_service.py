from typing import Dict, List, Any
import os
import base64
import re
from urllib.parse import urlparse
import aiohttp
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, access_token: str = None, installation_id: int = None):
        """Initialize GitHub service with access token or installation ID."""
        self.access_token = access_token
        self.installation_id = installation_id
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
    
    async def _get_installation_token(self) -> str:
        """Get fresh installation access token for GitHub App operations."""
        if not self.installation_id:
            raise ValueError("Installation ID required for GitHub App operations")
        
        from app.core.auth import get_installation_access_token
        return await get_installation_access_token(self.installation_id)

    def _parse_repo_url(self, repo_url: str) -> tuple:
        """Parse a GitHub repository URL to extract owner and repo name."""
        # Handle different URL formats
        if "github.com" in repo_url:
            path = urlparse(repo_url).path.strip("/")
        else:
            path = repo_url.strip("/")

        parts = path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    async def _github_request(
        self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None
    ) -> Dict:
        """Make a request to GitHub API."""
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=self.headers, params=params, json=data
                ) as response:
                    if response.status == 404:
                        raise ValueError(f"Resource not found: {url}")
                    elif response.status >= 400:
                        error_body = await response.text()
                        raise ValueError(
                            f"GitHub API error ({response.status}): {error_body}"
                        )

                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"GitHub API request failed: {str(e)}")
                raise ValueError(f"GitHub API request failed: {str(e)}")

    async def get_repository_details(self, repo_url: str) -> Dict[str, Any]:
        """Get detailed information about a GitHub repository."""
        owner, repo = self._parse_repo_url(repo_url)
        repo_data = await self._github_request(f"/repos/{owner}/{repo}")

        # Get repository topics
        topics_data = await self._github_request(f"/repos/{owner}/{repo}/topics")

        # Extract languages used
        languages_data = await self._github_request(f"/repos/{owner}/{repo}/languages")
        primary_language = repo_data.get("language")

        # Get contributor information
        contributors_data = await self._github_request(
            f"/repos/{owner}/{repo}/contributors"
        )
        contributors = [
            {"name": item["login"], "contributions": item["contributions"]}
            for item in contributors_data[:5]
        ]  # Limit to top 5 contributors

        return {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "language": primary_language,
            "languages": languages_data,
            "topics": topics_data.get("names", []),
            "homepage": repo_data.get("homepage"),
            "default_branch": repo_data.get("default_branch"),
            "license": (
                repo_data.get("license", {}).get("name")
                if repo_data.get("license")
                else None
            ),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "issues": repo_data.get("open_issues_count"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "contributors": contributors,
        }

    async def get_repository_file_structure(
        self, repo_url: str, path: str = "", max_depth: int = 3, max_files: int = 100
    ) -> str:
        """Get file structure of a GitHub repository with size limits."""
        owner, repo = self._parse_repo_url(repo_url)
        default_branch = (await self.get_repository_details(repo_url)).get(
            "default_branch", "main"
        )

        # Get contents of the repository at the specified path
        try:
            contents = await self._github_request(
                f"/repos/{owner}/{repo}/contents/{path}"
            )
        except ValueError as e:
            logger.error(f"Error getting repository contents: {str(e)}")
            return "Unable to retrieve file structure"

        if not isinstance(contents, list):
            return "Invalid repository path or structure"

        # Function to recursively build file structure with limits
        async def build_structure(
            items, prefix="", is_last=None, current_depth=1, file_count=0
        ):
            if is_last is None:
                is_last = [True]

            result = []
            total = len(items)

            # Sort items: directories first, then files alphabetically
            items.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))

            for i, item in enumerate(items):
                # Check if we've reached the file limit
                if file_count >= max_files:
                    if i < total - 1:
                        result.append(f"{prefix}... ({total - i} more items not shown)")
                    break

                is_last_item = i == total - 1
                current_prefix = prefix

                # Build the line prefix
                if prefix:
                    line_prefix = prefix + ("└── " if is_last_item else "├── ")
                else:
                    line_prefix = ""

                # Add the item
                result.append(f"{line_prefix}{item['name']}")

                # If file, increment the file counter
                if item["type"] == "file":
                    file_count += 1

                # If directory and not at max depth, get its contents recursively
                if item["type"] == "dir" and current_depth < max_depth:
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    try:
                        subcontents = await self._github_request(item["url"])
                        sub_result, file_count = await build_structure(
                            subcontents,
                            next_prefix,
                            current_depth=current_depth + 1,
                            file_count=file_count,
                        )
                        result.extend(sub_result)
                    except ValueError:
                        result.append(f"{next_prefix}(Error loading contents)")
                elif item["type"] == "dir" and current_depth >= max_depth:
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    result.append(
                        f"{next_prefix}... (directory content not shown due to depth limit)"
                    )

            return result, file_count

        structure_lines, _ = await build_structure(contents)

        # Add repository size information
        try:
            repo_data = await self._github_request(f"/repos/{owner}/{repo}")
            repo_size = repo_data.get("size", 0)  # Size in KB
            size_info = f"\nRepository size: {self._format_size(repo_size * 1024)}"
            structure_lines.append(size_info)
        except Exception:
            pass

        return "\n".join(structure_lines)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024 or unit == "TB":
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024

    async def get_optimized_repository_structure(self, repo_url: str) -> str:
        """Get an optimized view of repository structure focusing on important files."""
        owner, repo = self._parse_repo_url(repo_url)
        repo_details = await self.get_repository_details(repo_url)

    async def get_code_samples(self, repo_url: str) -> Dict[str, str]:
        """Get representative code samples from the repository."""
        owner, repo = self._parse_repo_url(repo_url)
        repo_details = await self.get_repository_details(repo_url)
        primary_language = (repo_details.get("language") or "").lower()
        default_branch = repo_details.get("default_branch", "main")

        # Determine file extensions to look for based on primary language
        extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx", ".ts", ".tsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c#": [".cs"],
            "c++": [".cpp", ".hpp", ".h"],
            "c": [".c", ".h"],
            "go": [".go"],
            "ruby": [".rb"],
            "php": [".php"],
            "rust": [".rs"],
            "kotlin": [".kt"],
            "swift": [".swift"],
        }.get(primary_language, [])

        # If we couldn't determine extensions, look for common file patterns
        if not extensions:
            extensions = [
                ".py",
                ".js",
                ".java",
                ".cpp",
                ".go",
                ".rs",
                ".rb",
                ".php",
                ".ts",
            ]

        # Try to find main entry points or readme files
        important_files = [
            "README.md",
            "setup.py",
            "requirements.txt",
            "pyproject.toml",  # Python
            "package.json",
            "tsconfig.json",  # JavaScript/TypeScript
            "pom.xml",
            "build.gradle",  # Java
            "Cargo.toml",  # Rust
            "go.mod",  # Go
            "Gemfile",  # Ruby
            "composer.json",  # PHP
        ]

        # Get tree of the repository
        trees_url = f"/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"

        try:
            tree_data = await self._github_request(trees_url)
            files = tree_data.get("tree", [])
        except ValueError:
            # Fallback if we can't get the tree
            return {"README.md": "Unable to retrieve code samples"}

        # Filter for relevant files
        code_files = [
            f
            for f in files
            if f["type"] == "blob"
            and (
                any(f["path"].endswith(ext) for ext in extensions)
                or f["path"] in important_files
            )
        ]

        # Sort by importance (entry points, readmes first)
        def file_priority(file):
            path = file["path"].lower()
            if any(
                path.endswith(f"/{name}") or path == name
                for name in ["main.py", "app.py", "index.js", "main.js", "app.js"]
            ):
                return 0
            if path in [f.lower() for f in important_files]:
                return 1
            if "/" not in path:  # Root-level files
                return 2
            return 3

        code_files.sort(key=file_priority)

        # Limit to max 5 files
        code_files = code_files[:5]
        samples = {}

        # Get content of each file
        for file in code_files:
            try:
                content_data = await self._github_request(
                    f"/repos/{owner}/{repo}/contents/{file['path']}"
                )
                if content_data.get("encoding") == "base64" and content_data.get(
                    "content"
                ):
                    content = base64.b64decode(content_data["content"]).decode("utf-8")
                    samples[file["path"]] = content
            except (ValueError, UnicodeDecodeError) as e:
                logger.warning(
                    f"Could not retrieve content for {file['path']}: {str(e)}"
                )

        return samples

    async def upload_file_to_repo(
        self,
        repo_url: str,
        file_path: str,
        content: str,
        commit_message: str = "Add README.md",
        branch: str = None,
    ) -> Dict:
        """Upload a file to a GitHub repository."""
        owner, repo = self._parse_repo_url(repo_url)

        # For GitHub App operations, get fresh installation token
        if self.installation_id:
            installation_token = await self._get_installation_token()
            headers = {
                **self.headers,
                "Authorization": f"token {installation_token}"
            }
        else:
            headers = self.headers

        if branch is None:
            repo_details = await self.get_repository_details(repo_url)
            branch = repo_details.get("default_branch", "main")

        # Check if file already exists
        try:
            existing_file = await self._github_request_with_headers(
                f"/repos/{owner}/{repo}/contents/{file_path}?ref={branch}",
                headers=headers
            )
            file_sha = existing_file.get("sha")
        except ValueError:
            file_sha = None

        # Prepare request data
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }

        if file_sha:
            data["sha"] = file_sha

        # Upload the file
        response = await self._github_request_with_headers(
            f"/repos/{owner}/{repo}/contents/{file_path}", 
            method="PUT", 
            data=data,
            headers=headers
        )

        return response
    
    async def get_repository_branches(self, repo_url: str) -> List[Dict[str, Any]]:
        """Get all branches from a GitHub repository."""
        owner, repo = self._parse_repo_url(repo_url)

        # For GitHub App operations, get fresh installation token
        if self.installation_id:
            installation_token = await self._get_installation_token()
            headers = {
                **self.headers,
                "Authorization": f"token {installation_token}"
            }
        else:
            headers = self.headers

        try:
            branches_data = await self._github_request_with_headers(
                f"/repos/{owner}/{repo}/branches",
                headers=headers
            )
            
            # Format branch data for frontend
            branches = []
            for branch in branches_data:
                branches.append({
                    "name": branch["name"],
                    "sha": branch["commit"]["sha"],
                    "protected": branch.get("protected", False),
                    "is_default": False  # We'll set this separately
                })
            
            # Get default branch info
            repo_details = await self.get_repository_details(repo_url)
            default_branch = repo_details.get("default_branch", "main")
            
            # Mark the default branch
            for branch in branches:
                if branch["name"] == default_branch:
                    branch["is_default"] = True
                    break
            
            # Sort branches: default first, then alphabetically
            branches.sort(key=lambda x: (not x["is_default"], x["name"]))
            
            return branches
            
        except ValueError as e:
            logger.error(f"Error getting repository branches: {str(e)}")
            # Return default branch as fallback
            repo_details = await self.get_repository_details(repo_url)
            return [{
                "name": repo_details.get("default_branch", "main"),
                "sha": "",
                "protected": False,
                "is_default": True
            }]

    async def create_branch(self, repo_url: str, branch_name: str, source_branch: str = None) -> Dict[str, Any]:
        """Create a new branch in the repository."""
        owner, repo = self._parse_repo_url(repo_url)

        # For GitHub App operations, get fresh installation token
        if self.installation_id:
            installation_token = await self._get_installation_token()
            headers = {
                **self.headers,
                "Authorization": f"token {installation_token}"
            }
        else:
            headers = self.headers

        # Get source branch SHA
        if source_branch is None:
            repo_details = await self.get_repository_details(repo_url)
            source_branch = repo_details.get("default_branch", "main")

        try:
            # Get source branch details
            source_branch_data = await self._github_request_with_headers(
                f"/repos/{owner}/{repo}/git/refs/heads/{source_branch}",
                headers=headers
            )
            source_sha = source_branch_data["object"]["sha"]

            # Create new branch
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": source_sha
            }

            response = await self._github_request_with_headers(
                f"/repos/{owner}/{repo}/git/refs",
                method="POST",
                data=data,
                headers=headers
            )

            return {
                "name": branch_name,
                "sha": response["object"]["sha"],
                "created": True
            }

        except ValueError as e:
            logger.error(f"Error creating branch: {str(e)}")
            raise ValueError(f"Failed to create branch '{branch_name}': {str(e)}")

    async def _github_request_with_headers(
        self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None, headers: dict = None
    ) -> Dict:
        """Make a request to GitHub API with custom headers."""
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or self.headers

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=request_headers, params=params, json=data
                ) as response:
                    if response.status == 404:
                        raise ValueError(f"Resource not found: {url}")
                    elif response.status >= 400:
                        error_body = await response.text()
                        raise ValueError(
                            f"GitHub API error ({response.status}): {error_body}"
                        )

                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"GitHub API request failed: {str(e)}")
                raise ValueError(f"GitHub API request failed: {str(e)}")
