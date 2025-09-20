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
    ReadmeHistoryResponse,
    ReadmeHistoryEntry,
)
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService
from app.api.deps import get_github_service, get_gemini_service, get_current_user
from app.exceptions import ReadmeGenerationException, GitHubException
from app.utils.repository_validation import validate_repository_access
from app.db.readme_history import (
    save_readme_to_history,
    get_user_readme_history,
    get_readme_history_entry,
    delete_readme_history_entry,
    get_user_readme_stats,
)

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

        owner, repo = await validate_repository_access(
            github_service, request.repository_url
        )

        request.repository_url = f"{owner}/{repo}"

        request.sections.sort(key=lambda x: x.order)

        content = await gemini_service.generate_readme(request, github_service)

        # Return the sections that were requested to be generated
        sections_generated = [section.name for section in request.sections]

        # Save to history
        repository_name = request.repository_url.split('/')[-1] if '/' in request.repository_url else request.repository_url
        await save_readme_to_history(
            username=username,
            repository_url=request.repository_url,
            repository_name=repository_name,
            content=content,
            sections_generated=sections_generated,
            generation_type="new"  # Could be "improved" if existing README was found
        )

        return ReadmeResponse(content=content, sections_generated=sections_generated)
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

        content = await gemini_service.refine_readme(request.content, request.feedback)

        # For refinement, parse the content to see what sections are present
        section_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
        sections_generated = section_pattern.findall(content)

        # Save refined README to history
        await save_readme_to_history(
            username=username,
            repository_url="manual-refinement",  # No specific repo for manual refinements
            repository_name="Manual Refinement",
            content=content,
            sections_generated=sections_generated,
            generation_type="refined"
        )

        return ReadmeResponse(content=content, sections_generated=sections_generated)
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

        owner, repo = await validate_repository_access(
            github_service, request.repository_url
        )

        request.repository_url = f"{owner}/{repo}"

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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
            tmp.write(content.encode("utf-8"))
            tmp_path = tmp.name

        response = FileResponse(
            path=tmp_path, media_type="text/markdown", filename=filename
        )

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

        await validate_repository_access(github_service, repo_url)

        repo_details = await github_service.get_repository_details(repo_url)

        file_structure = await github_service.get_repository_file_structure(repo_url)

        code_samples = await github_service.get_code_samples(repo_url)

        repo_info = {
            **repo_details,
            "file_structure": file_structure,
            "code_samples": code_samples,
        }

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

        await validate_repository_access(github_service, repo_url)

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

        await validate_repository_access(github_service, repo_url)

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

        await validate_repository_access(github_service, repo_url)

        repo_details = await github_service.get_repository_details(repo_url)

        file_structure = await github_service.get_repository_file_structure(repo_url)

        code_samples = await github_service.get_code_samples(repo_url)

        repo_info = {
            **repo_details,
            "file_structure": file_structure,
            "code_samples": code_samples,
        }

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

        analysis = await gemini_service.analyze_repository_for_readme(
            repo_info, files, code_samples
        )

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


@router.get("/history", response_model=ReadmeHistoryResponse)
async def get_readme_history(
    page: int = 1,
    page_size: int = 10,
    repository_filter: Optional[str] = None,
    username: str = Depends(get_current_user),
):
    """Get user's README generation history."""
    try:
        
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 50:
            page_size = 10
            
        result = await get_user_readme_history(
            username=username,
            page=page,
            page_size=page_size,
            repository_filter=repository_filter
        )
        
        return ReadmeHistoryResponse(**result)
        
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get README history: {str(e)}",
        )


@router.get("/history/{entry_id}", response_model=ReadmeHistoryEntry)
async def get_readme_history_entry(
    entry_id: str,
    username: str = Depends(get_current_user),
):
    """Get a specific README history entry."""
    try:
        
        entry = await get_readme_history_entry(entry_id, username)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="README history entry not found"
            )
            
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get README history entry: {str(e)}",
        )


@router.post("/history/{entry_id}/download")
async def download_readme_from_history(
    entry_id: str,
    filename: Optional[str] = None,
    username: str = Depends(get_current_user),
):
    """Download a README from history."""
    try:
        
        entry = await get_readme_history_entry(entry_id, username)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="README history entry not found"
            )
            
        # Generate filename if not provided
        if not filename:
            filename = f"{entry.repository_name}_README_{entry.created_at.strftime('%Y%m%d_%H%M%S')}.md"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
            tmp.write(entry.content.encode("utf-8"))
            tmp_path = tmp.name

        response = FileResponse(
            path=tmp_path, 
            media_type="text/markdown", 
            filename=filename
        )

        response.background = lambda: os.unlink(tmp_path)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download README from history: {str(e)}",
        )


@router.delete("/history/{entry_id}")
async def delete_readme_history_entry(
    entry_id: str,
    username: str = Depends(get_current_user),
):
    """Delete a README history entry."""
    try:
        
        deleted = await delete_readme_history_entry(entry_id, username)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="README history entry not found"
            )
            
        return {"message": "README history entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete README history entry: {str(e)}",
        )


@router.get("/history/stats/overview")
async def get_readme_stats(
    username: str = Depends(get_current_user),
):
    """Get README generation statistics for the user."""
    try:
        
        stats = await get_user_readme_stats(username)
        return stats
        
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get README statistics: {str(e)}",
        )
