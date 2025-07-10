from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
import tempfile
import os
import re

from app.schemas.readme import (
    ReadmeGenerationRequest,
    ReadmeResponse,
    ReadmeRefineRequest,
    ReadmeSaveRequest,
    SectionTemplate,
    DEFAULT_SECTION_TEMPLATES,
)
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService
from app.api.deps import get_github_service, get_gemini_service, get_current_user
from app.exceptions import ReadmeGenerationException, GitHubException
from app.utils.repository_validation import validate_repository_access


router = APIRouter(prefix="/readme")


@router.get("/sections", response_model=List[SectionTemplate])
async def get_section_templates():
    """Get available README section templates."""
    return DEFAULT_SECTION_TEMPLATES


@router.post("/generate", response_model=ReadmeResponse)
async def generate_readme(
    request: ReadmeGenerationRequest,
    github_service: GitHubService = Depends(get_github_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    username: str = Depends(get_current_user),
):
    """Generate a README for a GitHub repository."""
    try:
        # Validate repository access
        owner, repo = await validate_repository_access(
            github_service, request.repository_url
        )

        # Update repository URL to ensure consistent format
        request.repository_url = f"{owner}/{repo}"

        # Sort sections by order
        request.sections.sort(key=lambda x: x.order)

        # Generate README content
        content = await gemini_service.generate_readme(request, github_service)

        # Extract section headings from the content
        section_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
        sections_included = section_pattern.findall(content)

        return ReadmeResponse(content=content, sections_included=sections_included)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException) or isinstance(e, ReadmeGenerationException):
            raise e
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"README generation failed: {str(e)}",
        )


@router.post("/refine", response_model=ReadmeResponse)
async def refine_readme(
    request: ReadmeRefineRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
    username: str = Depends(get_current_user),
):
    """Refine an existing README based on feedback."""
    try:
        # Refine README content
        content = await gemini_service.refine_readme(request.content, request.feedback)

        # Extract section headings from the content
        section_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
        sections_included = section_pattern.findall(content)

        return ReadmeResponse(content=content, sections_included=sections_included)
    except Exception as e:
        if isinstance(e, ReadmeGenerationException):
            raise e
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"README refinement failed: {str(e)}",
        )


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_readme_to_github(
    request: ReadmeSaveRequest,
    github_service: GitHubService = Depends(get_github_service),
    username: str = Depends(get_current_user),
):
    """Save a README to a GitHub repository."""
    try:
        # Validate repository access
        owner, repo = await validate_repository_access(
            github_service, request.repository_url
        )

        # Update repository URL to ensure consistent format
        request.repository_url = f"{owner}/{repo}"

        # Upload README to GitHub
        response = await github_service.upload_file_to_repo(
            repo_url=request.repository_url,
            file_path=request.path,
            content=request.content,
            commit_message=request.commit_message,
            branch=request.branch,
        )

        return {
            "message": f"README successfully saved to {request.repository_url}",
            "commit": response,
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException):
            raise e
        raise GitHubException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save README: {str(e)}",
        )


@router.post("/download", status_code=status.HTTP_200_OK)
async def download_readme(
    content: str, filename: str = "README.md", username: str = Depends(get_current_user)
):
    """Download README as a Markdown file."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
            tmp.write(content.encode("utf-8"))
            tmp_path = tmp.name

        # Return the file as a download
        response = FileResponse(
            path=tmp_path, media_type="text/markdown", filename=filename
        )

        # Set up file cleanup after download
        response.background = lambda: os.unlink(tmp_path)

        return response
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download README: {str(e)}",
        )


@router.get("/preview/{owner}/{repo}")
async def preview_generated_readme(
    owner: str,
    repo: str,
    sections: Optional[List[str]] = None,
    github_service: GitHubService = Depends(get_github_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    username: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Preview what sections would be included and analyze repository structure.
    This is a helper endpoint for development and debugging.
    """
    try:
        repo_url = f"{owner}/{repo}"

        # Validate repository access
        # This will raise HTTPException if access is denied
        await validate_repository_access(github_service, repo_url)

        # Get repository details
        repo_details = await github_service.get_repository_details(repo_url)

        # Get file structure
        file_structure = await github_service.get_repository_file_structure(repo_url)

        # Get code samples
        code_samples = await github_service.get_code_samples(repo_url)

        # Combine all info
        repo_info = {
            **repo_details,
            "file_structure": file_structure,
            "code_samples": code_samples,
        }

        # Analyze repository to recommend sections
        analysis = await gemini_service.analyze_repository_for_readme(repo_info, [], {})

        return {
            "repository": {
                "name": repo_details["name"],
                "full_name": repo_details["full_name"],
                "description": repo_details.get("description"),
                "language": repo_details.get("language"),
                "stars": repo_details.get("stars"),
                "forks": repo_details.get("forks"),
            },
            "recommended_sections": analysis["recommended_sections"],
            "custom_sections": analysis["custom_sections"],
            "file_structure_preview": (
                file_structure[:500] + "..."
                if len(file_structure) > 500
                else file_structure
            ),
            "code_samples_found": list(code_samples.keys()),
            "analysis": analysis["analysis"],
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException) or isinstance(e, ReadmeGenerationException):
            raise e
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview README generation: {str(e)}",
        )


@router.get("/branches/{owner}/{repo}")
async def get_repository_branches(
    owner: str,
    repo: str,
    github_service: GitHubService = Depends(get_github_service),
    username: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all branches from a repository for user selection."""
    try:
        repo_url = f"{owner}/{repo}"
        
        # Validate repository access
        await validate_repository_access(github_service, repo_url)
        
        # Get branches
        branches = await github_service.get_repository_branches(repo_url)
        
        return {
            "repository": f"{owner}/{repo}",
            "branches": branches,
            "total_count": len(branches)
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException):
            raise e
        raise GitHubException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository branches: {str(e)}",
        )


@router.post("/branches/{owner}/{repo}")
async def create_repository_branch(
    owner: str,
    repo: str,
    branch_name: str,
    source_branch: Optional[str] = None,
    github_service: GitHubService = Depends(get_github_service),
    username: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new branch in the repository."""
    try:
        repo_url = f"{owner}/{repo}"
        
        # Validate repository access
        await validate_repository_access(github_service, repo_url)
        
        # Create branch
        result = await github_service.create_branch(repo_url, branch_name, source_branch)
        
        return {
            "message": f"Branch '{branch_name}' created successfully",
            "branch": result,
            "repository": f"{owner}/{repo}"
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException):
            raise e
        raise GitHubException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}",
        )


@router.get("/analyze/{owner}/{repo}")
async def analyze_repository(
    owner: str,
    repo: str,
    github_service: GitHubService = Depends(get_github_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    username: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Analyze a repository to recommend README sections and structure.
    """
    try:
        repo_url = f"{owner}/{repo}"

        # Validate repository access
        # This will raise HTTPException if access is denied
        await validate_repository_access(github_service, repo_url)

        # Get repository details
        repo_details = await github_service.get_repository_details(repo_url)

        # Get file structure
        file_structure = await github_service.get_repository_file_structure(repo_url)

        # Get code samples
        code_samples = await github_service.get_code_samples(repo_url)

        # Combine all info
        repo_info = {
            **repo_details,
            "file_structure": file_structure,
            "code_samples": code_samples,
        }

        # Extract files for analysis
        files = []
        for file_path in code_samples.keys():
            files.append(
                {
                    "path": file_path,
                    "type": "file",
                    "size": len(code_samples[file_path]),
                    "name": file_path.split("/")[-1],
                }
            )

        # Analyze repository to recommend sections
        analysis = await gemini_service.analyze_repository_for_readme(
            repo_info, files, code_samples
        )

        # Convert recommended sections to template format
        recommended_templates = []
        for i, section in enumerate(analysis["recommended_sections"]):
            recommended_templates.append(
                SectionTemplate(
                    id=section["id"],
                    name=section["name"],
                    description=f"Recommended section for this repository",
                    is_default=True,
                    order=i + 1,
                )
            )

        # Add custom sections
        for i, section_name in enumerate(analysis["custom_sections"]):
            custom_id = f"custom_{i+1}"
            recommended_templates.append(
                SectionTemplate(
                    id=custom_id,
                    name=section_name,
                    description=f"Custom section for this repository",
                    is_default=False,
                    order=len(recommended_templates) + i + 1,
                )
            )

        return {
            "repository": {
                "name": repo_details["name"],
                "full_name": repo_details["full_name"],
                "description": repo_details.get("description"),
                "language": repo_details.get("language"),
                "stars": repo_details.get("stars"),
                "forks": repo_details.get("forks"),
            },
            "recommended_sections": recommended_templates,
            "analysis": analysis["analysis"],
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, GitHubException) or isinstance(e, ReadmeGenerationException):
            raise e
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze repository: {str(e)}",
        )
