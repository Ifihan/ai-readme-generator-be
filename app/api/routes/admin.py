from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_admin_user
from app.exceptions import ReadmeGenerationException
from app.db.admin import set_user_admin, get_admin_users, check_user_admin
from app.db.users import get_user_by_username

router = APIRouter(prefix="/admin")


class AdminUserResponse(BaseModel):
    """Response model for admin user info."""
    username: str
    email: str = None
    full_name: str = None
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin_user",
                "email": "admin@example.com",
                "full_name": "Admin User",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class AdminUsersListResponse(BaseModel):
    """Response model for list of admin users."""
    admin_users: List[AdminUserResponse]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "admin_users": [
                    {
                        "username": "admin_user",
                        "email": "admin@example.com", 
                        "full_name": "Admin User",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


@router.post("/users/{username}/make-admin", response_model=MessageResponse)
async def make_user_admin(
    username: str,
    admin_username: str = Depends(get_admin_user),
):
    """Make a user admin (admin only)."""
    try:
        # Check if target user exists
        target_user = await get_user_by_username(username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found. User must log in at least once before being made admin."
            )
        
        # Check if user is already admin
        if target_user.get("is_admin", False):
            return MessageResponse(message=f"User '{username}' is already an admin")
        
        # Make user admin
        success = await set_user_admin(username, True)
        if not success:
            raise ReadmeGenerationException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make user '{username}' admin"
            )
        
        return MessageResponse(message=f"Successfully made user '{username}' an admin")
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to make user admin: {str(e)}"
        )


@router.delete("/users/{username}/remove-admin", response_model=MessageResponse)
async def remove_user_admin(
    username: str,
    admin_username: str = Depends(get_admin_user),
):
    """Remove admin privileges from a user (admin only)."""
    try:
        # Prevent self-removal of admin privileges
        if username == admin_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin privileges from yourself"
            )
        
        # Check if target user exists
        target_user = await get_user_by_username(username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )
        
        # Check if user is admin
        if not target_user.get("is_admin", False):
            return MessageResponse(message=f"User '{username}' is not an admin")
        
        # Remove admin privileges
        success = await set_user_admin(username, False)
        if not success:
            raise ReadmeGenerationException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove admin privileges from user '{username}'"
            )
        
        return MessageResponse(message=f"Successfully removed admin privileges from user '{username}'")
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove admin privileges: {str(e)}"
        )


@router.get("/users", response_model=AdminUsersListResponse)
async def list_admin_users(
    admin_username: str = Depends(get_admin_user),
):
    """List all admin users (admin only)."""
    try:
        admin_users = await get_admin_users()
        
        response_users = []
        for user in admin_users:
            response_users.append(AdminUserResponse(
                username=user["username"],
                email=user.get("email", ""),
                full_name=user.get("full_name", ""),
                created_at=user["created_at"].isoformat() if user.get("created_at") else ""
            ))
        
        return AdminUsersListResponse(
            admin_users=response_users,
            total_count=len(response_users)
        )
        
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list admin users: {str(e)}"
        )


@router.get("/users/{username}/status")
async def check_admin_status(
    username: str,
    admin_username: str = Depends(get_admin_user),
):
    """Check if a user has admin privileges (admin only)."""
    try:
        # Check if target user exists
        target_user = await get_user_by_username(username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )
        
        is_admin = target_user.get("is_admin", False)
        
        return {
            "username": username,
            "is_admin": is_admin,
            "status": "admin" if is_admin else "regular_user"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise ReadmeGenerationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check admin status: {str(e)}"
        )