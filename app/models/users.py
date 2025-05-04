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
    username: str, installation_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new user in MongoDB."""
    db = get_database()

    # Check if user already exists
    existing_user = await db.users.find_one({"username": username})

    if existing_user:
        # Update installation_id and last_login if user exists
        await db.users.update_one(
            {"username": username},
            {
                "$set": {
                    "installation_id": installation_id,
                    "last_login": datetime.utcnow(),
                }
            },
        )
        updated_user = await db.users.find_one({"username": username})
        return user_helper(updated_user)

    # Create new user
    user_data = {
        "username": username,
        "installation_id": installation_id,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
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
