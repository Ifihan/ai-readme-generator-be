from typing import Dict, Any, Optional
from app.db.mongodb import get_database
from app.db.users import get_user_by_username


async def set_user_admin(username: str, is_admin: bool = True) -> bool:
    """Set admin status for a user."""
    db = get_database()
    
    # Check if user exists
    user = await get_user_by_username(username)
    if not user:
        return False
    
    # Update admin status
    result = await db.users.update_one(
        {"username": username},
        {"$set": {"is_admin": is_admin}}
    )
    
    return result.modified_count > 0


async def get_admin_users() -> list[Dict[str, Any]]:
    """Get all admin users."""
    db = get_database()
    
    admin_users = []
    cursor = db.users.find({"is_admin": True})
    
    async for user in cursor:
        admin_users.append({
            "username": user["username"],
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "created_at": user["created_at"]
        })
    
    return admin_users


async def check_user_admin(username: str) -> bool:
    """Check if a user has admin privileges."""
    user = await get_user_by_username(username)
    return user.get("is_admin", False) if user else False