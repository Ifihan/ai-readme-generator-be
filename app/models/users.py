from datetime import datetime
from typing import Optional, Dict, List, Any

from app.db.mongodb import get_database
from app.models.mongodb_models import user_helper


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username from MongoDB."""
    db = get_database()
    user = await db.users.find_one({"username": username})

    if user:
        return user_helper(user)
    return None


async def create_user(
    username: str, 
    installation_id: Optional[int] = None,
    github_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new user in MongoDB with GitHub profile data."""
    db = get_database()

    # Check if user already exists
    existing_user = await db.users.find_one({"username": username})

    update_data = {
        "installation_id": installation_id,
        "last_login": datetime.utcnow(),
    }

    # Add GitHub profile data if provided
    if github_data:
        update_data.update({
            "email": github_data.get("email"),
            "full_name": github_data.get("name"),
            "avatar_url": github_data.get("avatar_url"),
            "github_id": github_data.get("id"),
            "public_repos": github_data.get("public_repos"),
            "company": github_data.get("company"),
        })

    if existing_user:
        # Update existing user with new data
        await db.users.update_one(
            {"username": username},
            {"$set": update_data}
        )
        updated_user = await db.users.find_one({"username": username})
        return user_helper(updated_user)

    # Create new user
    user_data = {
        "username": username,
        "installation_id": installation_id,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "email": github_data.get("email") if github_data else None,
        "full_name": github_data.get("name") if github_data else None,
        "avatar_url": github_data.get("avatar_url") if github_data else None,
        "github_id": github_data.get("id") if github_data else None,
        "public_repos": github_data.get("public_repos") if github_data else None,
        "company": github_data.get("company") if github_data else None,
    }

    result = await db.users.insert_one(user_data)
    new_user = await db.users.find_one({"_id": result.inserted_id})
    return user_helper(new_user)


async def update_user(username: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user in MongoDB."""
    db = get_database()

    user = await db.users.find_one({"username": username})
    if not user:
        return None

    # Update user with new data
    await db.users.update_one({"username": username}, {"$set": data})

    updated_user = await db.users.find_one({"username": username})
    return user_helper(updated_user)


async def delete_user(username: str) -> bool:
    """Delete user from MongoDB."""
    db = get_database()
    result = await db.users.delete_one({"username": username})
    return result.deleted_count > 0


async def list_users(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """List users from MongoDB with pagination."""
    db = get_database()
    users = []

    cursor = db.users.find().skip(skip).limit(limit)
    async for user in cursor:
        users.append(user_helper(user))

    return users
