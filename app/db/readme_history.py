from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import DESCENDING

from app.db.mongodb import get_database
from app.schemas.readme import ReadmeHistoryEntry


async def save_readme_to_history(
    username: str,
    repository_url: str,
    repository_name: str,
    content: str,
    sections_generated: List[str],
    generation_type: str = "new"
) -> str:
    """Save a generated README to user's history."""
    db = get_database()
    collection = db.readme_history
    
    history_entry = {
        "username": username,
        "repository_url": repository_url,
        "repository_name": repository_name,
        "content": content,
        "sections_generated": sections_generated,
        "generation_type": generation_type,
        "created_at": datetime.utcnow(),
        "file_size": len(content.encode('utf-8'))
    }
    
    result = await collection.insert_one(history_entry)
    return str(result.inserted_id)


async def get_user_readme_history(
    username: str,
    page: int = 1,
    page_size: int = 10,
    repository_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Get paginated README history for a user."""
    db = get_database()
    collection = db.readme_history
    
    # Build query
    query = {"username": username}
    if repository_filter:
        query["repository_name"] = {"$regex": repository_filter, "$options": "i"}
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get total count
    total_count = await collection.count_documents(query)
    
    # Get paginated results (including content for UI)
    cursor = collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(page_size)
    entries = await cursor.to_list(length=page_size)
    
    # Convert ObjectId to string
    for entry in entries:
        entry["id"] = str(entry["_id"])
        del entry["_id"]
    
    return {
        "entries": entries,
        "total_count": total_count,
        "page": page,
        "page_size": page_size
    }


async def get_readme_history_entry(entry_id: str, username: str) -> Optional[ReadmeHistoryEntry]:
    """Get a specific README history entry by ID."""
    from bson import ObjectId
    
    db = get_database()
    collection = db.readme_history
    
    try:
        entry = await collection.find_one({
            "_id": ObjectId(entry_id),
            "username": username
        })
        
        if entry:
            entry["id"] = str(entry["_id"])
            del entry["_id"]
            return ReadmeHistoryEntry(**entry)
            
    except Exception:
        return None
    
    return None


async def delete_readme_history_entry(entry_id: str, username: str) -> bool:
    """Delete a README history entry."""
    from bson import ObjectId
    
    db = get_database()
    collection = db.readme_history
    
    try:
        result = await collection.delete_one({
            "_id": ObjectId(entry_id),
            "username": username
        })
        return result.deleted_count > 0
    except Exception:
        return False


async def get_user_readme_stats(username: str) -> Dict[str, Any]:
    """Get README generation statistics for a user."""
    db = get_database()
    collection = db.readme_history
    
    # Basic counts
    total_generated = await collection.count_documents({"username": username})
    
    # Count by generation type
    pipeline = [
        {"$match": {"username": username}},
        {"$group": {
            "_id": "$generation_type",
            "count": {"$sum": 1}
        }}
    ]
    
    type_counts = {}
    async for doc in collection.aggregate(pipeline):
        type_counts[doc["_id"]] = doc["count"]
    
    # Recent activity (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = await collection.count_documents({
        "username": username,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    return {
        "total_generated": total_generated,
        "generation_types": type_counts,
        "recent_activity": recent_count
    }