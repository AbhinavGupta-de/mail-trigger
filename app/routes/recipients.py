from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.database import get_database
from app.models.recipient import RecipientCreate, RecipientUpdate, RecipientResponse

router = APIRouter(prefix="/api/recipients", tags=["recipients"])


@router.get("", response_model=List[RecipientResponse])
async def get_recipients(user=Depends(get_current_user)):
    """Get all recipients for current user."""
    db = get_database()
    recipients = await db.recipients.find({"user_id": str(user["_id"])}).to_list(100)

    return [
        RecipientResponse(
            id=str(r["_id"]),
            name=r["name"],
            email=r["email"],
            type=r["type"],
            is_default=r.get("is_default", False),
            created_at=r["created_at"]
        )
        for r in recipients
    ]


@router.get("/defaults")
async def get_default_recipients(user=Depends(get_current_user)):
    """Get default TO and CC recipients."""
    db = get_database()
    recipients = await db.recipients.find({
        "user_id": str(user["_id"]),
        "is_default": True
    }).to_list(100)

    to_recipients = [r for r in recipients if r["type"] == "to"]
    cc_recipients = [r for r in recipients if r["type"] == "cc"]

    return {
        "to": [{"name": r["name"], "email": r["email"]} for r in to_recipients],
        "cc": [{"name": r["name"], "email": r["email"]} for r in cc_recipients]
    }


@router.post("", response_model=RecipientResponse)
async def create_recipient(recipient: RecipientCreate, user=Depends(get_current_user)):
    """Create a new recipient."""
    db = get_database()

    new_recipient = {
        "user_id": str(user["_id"]),
        "name": recipient.name,
        "email": recipient.email,
        "type": recipient.type.value,
        "is_default": recipient.is_default,
        "created_at": datetime.utcnow()
    }

    result = await db.recipients.insert_one(new_recipient)

    return RecipientResponse(
        id=str(result.inserted_id),
        name=new_recipient["name"],
        email=new_recipient["email"],
        type=new_recipient["type"],
        is_default=new_recipient["is_default"],
        created_at=new_recipient["created_at"]
    )


@router.put("/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    recipient_id: str,
    recipient: RecipientUpdate,
    user=Depends(get_current_user)
):
    """Update a recipient."""
    db = get_database()

    existing = await db.recipients.find_one({
        "_id": ObjectId(recipient_id),
        "user_id": str(user["_id"])
    })

    if not existing:
        raise HTTPException(status_code=404, detail="Recipient not found")

    update_data = recipient.model_dump(exclude_unset=True)

    if "type" in update_data and update_data["type"]:
        update_data["type"] = update_data["type"].value

    await db.recipients.update_one(
        {"_id": ObjectId(recipient_id)},
        {"$set": update_data}
    )

    updated = await db.recipients.find_one({"_id": ObjectId(recipient_id)})

    return RecipientResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        email=updated["email"],
        type=updated["type"],
        is_default=updated.get("is_default", False),
        created_at=updated["created_at"]
    )


@router.delete("/{recipient_id}")
async def delete_recipient(recipient_id: str, user=Depends(get_current_user)):
    """Delete a recipient."""
    db = get_database()

    result = await db.recipients.delete_one({
        "_id": ObjectId(recipient_id),
        "user_id": str(user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipient not found")

    return {"message": "Recipient deleted successfully"}
