from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.readme import (
    FeedbackCreateRequest,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackStats,
)
from app.api.deps import get_current_user, get_admin_user
from app.exceptions import ReadmeGenerationException
from app.db.feedback import (
    create_feedback,
    get_feedback_by_id,
    get_user_feedback,
    get_feedback_by_readme_history_id,
    update_feedback,
    delete_feedback,
    get_feedback_stats,
)
from app.db.readme_history import get_readme_history_entry

router = APIRouter(prefix="/feedback")


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackCreateRequest,
    username: str = Depends(get_current_user),
):
    """Submit feedback for a README generation."""
    try:
        # Verify that the README history entry exists and belongs to the user
        readme_entry = await get_readme_history_entry(
            request.readme_history_id, username
        )
        if not readme_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="README history entry not found",
            )

        # Check if feedback already exists for this README
        existing_feedback = await get_feedback_by_readme_history_id(
            request.readme_history_id, username
        )
        if existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feedback already exists for this README. Use PUT to update.",
            )

        # Create the feedback
        feedback_id = await create_feedback(
            username=username,
            request=request,
            repository_name=readme_entry.repository_name,
        )

        # Return the created feedback
        feedback = await get_feedback_by_id(feedback_id, username)
        if not feedback:
            raise ReadmeGenerationException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created feedback",
            )

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )


@router.get("/", response_model=FeedbackListResponse)
async def get_my_feedback(
    page: int = 1,
    page_size: int = 10,
    repository_filter: Optional[str] = None,
    username: str = Depends(get_current_user),
):
    """Get user's feedback history."""
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 50:
            page_size = 10

        result = await get_user_feedback(
            username=username,
            page=page,
            page_size=page_size,
            repository_filter=repository_filter,
        )

        return FeedbackListResponse(**result)

    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}",
        )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    username: str = Depends(get_current_user),
):
    """Get a specific feedback entry."""
    try:
        feedback = await get_feedback_by_id(feedback_id, username)
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
            )

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}",
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_user_feedback(
    feedback_id: str,
    request: FeedbackCreateRequest,
    username: str = Depends(get_current_user),
):
    """Update an existing feedback entry."""
    try:
        # Verify the feedback exists and belongs to the user
        existing_feedback = await get_feedback_by_id(feedback_id, username)
        if not existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
            )

        # Update the feedback
        updated = await update_feedback(feedback_id, username, request)
        if not updated:
            raise ReadmeGenerationException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update feedback",
            )

        # Return the updated feedback
        feedback = await get_feedback_by_id(feedback_id, username)
        if not feedback:
            raise ReadmeGenerationException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated feedback",
            )

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}",
        )


@router.delete("/{feedback_id}")
async def delete_user_feedback(
    feedback_id: str,
    username: str = Depends(get_current_user),
):
    """Delete a feedback entry."""
    try:
        deleted = await delete_feedback(feedback_id, username)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
            )

        return {"message": "Feedback deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}",
        )


@router.get("/readme/{readme_history_id}", response_model=FeedbackResponse)
async def get_feedback_for_readme(
    readme_history_id: str,
    username: str = Depends(get_current_user),
):
    """Get feedback for a specific README history entry."""
    try:
        # Verify that the README history entry exists and belongs to the user
        readme_entry = await get_readme_history_entry(readme_history_id, username)
        if not readme_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="README history entry not found",
            )

        feedback = await get_feedback_by_readme_history_id(readme_history_id, username)
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback found for this README",
            )

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback for README: {str(e)}",
        )


@router.get("/stats/overview", response_model=FeedbackStats)
async def get_user_feedback_stats(
    username: str = Depends(get_current_user),
):
    """Get feedback statistics for the current user."""
    try:
        stats = await get_feedback_stats(username=username)
        return FeedbackStats(**stats)

    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback statistics: {str(e)}",
        )


@router.get("/stats/global", response_model=FeedbackStats)
async def get_global_feedback_stats(
    admin_username: str = Depends(get_admin_user),
):
    """Get global feedback statistics (admin only)."""
    try:
        stats = await get_feedback_stats(username=None)
        return FeedbackStats(**stats)

    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get global feedback statistics: {str(e)}",
        )
