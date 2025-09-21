from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo import DESCENDING

from app.db.mongodb import get_database
from app.models.mongodb_models import feedback_helper
from app.schemas.readme import FeedbackCreateRequest, FeedbackResponse


async def create_feedback(
    username: str,
    request: FeedbackCreateRequest,
    repository_name: str
) -> str:
    """Create a new feedback entry."""
    db = get_database()
    collection = db.feedback
    
    feedback_data = {
        "username": username,
        "readme_history_id": request.readme_history_id,
        "repository_name": repository_name,
        "rating": request.rating.value,
        "helpful_sections": request.helpful_sections or [],
        "problematic_sections": request.problematic_sections or [],
        "general_comments": request.general_comments or "",
        "suggestions": request.suggestions or "",
        "created_at": datetime.utcnow(),
    }
    
    result = await collection.insert_one(feedback_data)
    return str(result.inserted_id)


async def get_feedback_by_id(feedback_id: str, username: str) -> Optional[FeedbackResponse]:
    """Get a specific feedback entry by ID."""
    from bson import ObjectId
    
    db = get_database()
    collection = db.feedback
    
    try:
        feedback = await collection.find_one({
            "_id": ObjectId(feedback_id),
            "username": username
        })
        
        if feedback:
            return FeedbackResponse(**feedback_helper(feedback))
    except Exception:
        return None
    
    return None


async def get_user_feedback(
    username: str,
    page: int = 1,
    page_size: int = 10,
    repository_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Get paginated feedback for a user."""
    db = get_database()
    collection = db.feedback
    
    # Build query
    query = {"username": username}
    if repository_filter:
        query["repository_name"] = {"$regex": repository_filter, "$options": "i"}
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get total count
    total_count = await collection.count_documents(query)
    
    # Get paginated results
    cursor = collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(page_size)
    feedback_entries = []
    
    async for feedback in cursor:
        feedback_entries.append(FeedbackResponse(**feedback_helper(feedback)))
    
    return {
        "feedback": feedback_entries,
        "total_count": total_count,
        "page": page,
        "page_size": page_size
    }


async def get_feedback_by_readme_history_id(
    readme_history_id: str,
    username: str
) -> Optional[FeedbackResponse]:
    """Get feedback for a specific README history entry."""
    db = get_database()
    collection = db.feedback
    
    feedback = await collection.find_one({
        "readme_history_id": readme_history_id,
        "username": username
    })
    
    if feedback:
        return FeedbackResponse(**feedback_helper(feedback))
    
    return None


async def update_feedback(
    feedback_id: str,
    username: str,
    request: FeedbackCreateRequest
) -> bool:
    """Update an existing feedback entry."""
    from bson import ObjectId
    
    db = get_database()
    collection = db.feedback
    
    try:
        update_data = {
            "rating": request.rating.value,
            "helpful_sections": request.helpful_sections or [],
            "problematic_sections": request.problematic_sections or [],
            "general_comments": request.general_comments or "",
            "suggestions": request.suggestions or "",
        }
        
        result = await collection.update_one(
            {"_id": ObjectId(feedback_id), "username": username},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    except Exception:
        return False


async def delete_feedback(feedback_id: str, username: str) -> bool:
    """Delete a feedback entry."""
    from bson import ObjectId
    
    db = get_database()
    collection = db.feedback
    
    try:
        result = await collection.delete_one({
            "_id": ObjectId(feedback_id),
            "username": username
        })
        return result.deleted_count > 0
    except Exception:
        return False


async def get_feedback_stats(username: Optional[str] = None) -> Dict[str, Any]:
    """Get feedback statistics. If username is provided, get stats for that user only."""
    db = get_database()
    collection = db.feedback
    
    # Build base query
    base_query = {}
    if username:
        base_query["username"] = username
    
    # Basic counts
    total_feedback = await collection.count_documents(base_query)
    
    if total_feedback == 0:
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "most_helpful_sections": [],
            "most_problematic_sections": [],
            "recent_feedback_count": 0
        }
    
    # Average rating and rating distribution
    rating_pipeline = [
        {"$match": base_query},
        {"$group": {
            "_id": "$rating",
            "count": {"$sum": 1}
        }}
    ]
    
    rating_distribution = {}
    rating_values = {"excellent": 5, "good": 4, "average": 3, "poor": 2, "terrible": 1}
    total_rating_points = 0
    
    async for doc in collection.aggregate(rating_pipeline):
        rating = doc["_id"]
        count = doc["count"]
        rating_distribution[rating] = count
        total_rating_points += rating_values.get(rating, 0) * count
    
    average_rating = total_rating_points / total_feedback if total_feedback > 0 else 0
    
    # Most helpful sections
    helpful_pipeline = [
        {"$match": base_query},
        {"$unwind": "$helpful_sections"},
        {"$group": {
            "_id": "$helpful_sections",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    most_helpful_sections = []
    async for doc in collection.aggregate(helpful_pipeline):
        most_helpful_sections.append({
            "section": doc["_id"],
            "count": doc["count"]
        })
    
    # Most problematic sections
    problematic_pipeline = [
        {"$match": base_query},
        {"$unwind": "$problematic_sections"},
        {"$group": {
            "_id": "$problematic_sections",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    most_problematic_sections = []
    async for doc in collection.aggregate(problematic_pipeline):
        most_problematic_sections.append({
            "section": doc["_id"],
            "count": doc["count"]
        })
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_query = {**base_query, "created_at": {"$gte": thirty_days_ago}}
    recent_feedback_count = await collection.count_documents(recent_query)
    
    return {
        "total_feedback": total_feedback,
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution,
        "most_helpful_sections": most_helpful_sections,
        "most_problematic_sections": most_problematic_sections,
        "recent_feedback_count": recent_feedback_count
    }


async def get_all_feedback_for_analysis(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Get all feedback entries for analysis purposes (admin function)."""
    db = get_database()
    collection = db.feedback
    
    # Build query
    query = {}
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["created_at"] = date_query
    
    feedback_entries = []
    cursor = collection.find(query).sort("created_at", DESCENDING)
    
    async for feedback in cursor:
        feedback_entries.append(feedback_helper(feedback))
    
    return feedback_entries