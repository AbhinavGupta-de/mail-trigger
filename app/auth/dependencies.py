from fastapi import Request, HTTPException, Depends
from app.database import get_database
from bson import ObjectId
from datetime import datetime


async def get_current_user(request: Request):
    """Get current user from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(request: Request):
    """Get current user from session (optional - returns None if not logged in)."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return user


async def get_admin_user(request: Request):
    """Get current user and verify they are an admin."""
    user = await get_current_user(request)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
