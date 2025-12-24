from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from datetime import datetime
import re

from app.auth.dependencies import get_admin_user
from app.database import get_database
from app.models.template import TemplateCreate, TemplateUpdate, TemplateResponse
from app.models.recipient import RecipientCreate, RecipientUpdate, RecipientResponse
from app.models.user import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


def extract_variables(text: str) -> List[str]:
    """Extract template variables like {{variable}} from text."""
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, text)
    return list(set(matches))


# ==================== USER MANAGEMENT ====================

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin=Depends(get_admin_user)):
    """Get all users (admin only)."""
    db = get_database()
    users = await db.users.find().to_list(1000)

    return [
        UserResponse(
            id=str(u["_id"]),
            email=u["email"],
            name=u["name"],
            is_admin=u.get("is_admin", False),
            created_at=u["created_at"]
        )
        for u in users
    ]


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin=Depends(get_admin_user)):
    """Delete a user and all their data (admin only)."""
    db = get_database()

    # Don't allow deleting yourself
    if str(admin["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Delete user's templates, recipients, email logs, and the user
    await db.templates.delete_many({"user_id": user_id})
    await db.recipients.delete_many({"user_id": user_id})
    await db.email_logs.delete_many({"user_id": user_id})

    result = await db.users.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User and all related data deleted successfully"}


# ==================== GLOBAL TEMPLATES ====================

@router.get("/templates", response_model=List[TemplateResponse])
async def get_all_templates(admin=Depends(get_admin_user)):
    """Get all templates from all users (admin only)."""
    db = get_database()
    templates = await db.templates.find().to_list(1000)

    return [
        TemplateResponse(
            id=str(t["_id"]),
            name=t["name"],
            category=t["category"],
            subject=t["subject"],
            body=t["body"],
            variables=t.get("variables", []),
            is_default=t.get("is_default", False),
            created_at=t["created_at"]
        )
        for t in templates
    ]


@router.get("/templates/user/{user_id}", response_model=List[TemplateResponse])
async def get_user_templates(user_id: str, admin=Depends(get_admin_user)):
    """Get all templates for a specific user (admin only)."""
    db = get_database()
    templates = await db.templates.find({"user_id": user_id}).to_list(100)

    return [
        TemplateResponse(
            id=str(t["_id"]),
            name=t["name"],
            category=t["category"],
            subject=t["subject"],
            body=t["body"],
            variables=t.get("variables", []),
            is_default=t.get("is_default", False),
            created_at=t["created_at"]
        )
        for t in templates
    ]


@router.post("/templates/user/{user_id}", response_model=TemplateResponse)
async def create_template_for_user(
    user_id: str,
    template: TemplateCreate,
    admin=Depends(get_admin_user)
):
    """Create a template for a specific user (admin only)."""
    db = get_database()

    # Verify user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    variables = extract_variables(template.subject + " " + template.body)

    new_template = {
        "user_id": user_id,
        "name": template.name,
        "category": template.category.value,
        "subject": template.subject,
        "body": template.body,
        "variables": variables,
        "is_default": template.is_default,
        "created_at": datetime.utcnow()
    }

    if template.is_default:
        await db.templates.update_many(
            {"user_id": user_id},
            {"$set": {"is_default": False}}
        )

    result = await db.templates.insert_one(new_template)

    return TemplateResponse(
        id=str(result.inserted_id),
        name=new_template["name"],
        category=new_template["category"],
        subject=new_template["subject"],
        body=new_template["body"],
        variables=variables,
        is_default=new_template["is_default"],
        created_at=new_template["created_at"]
    )


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_any_template(
    template_id: str,
    template: TemplateUpdate,
    admin=Depends(get_admin_user)
):
    """Update any template (admin only)."""
    db = get_database()

    existing = await db.templates.find_one({"_id": ObjectId(template_id)})

    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = template.model_dump(exclude_unset=True)

    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].value

    new_subject = update_data.get("subject", existing["subject"])
    new_body = update_data.get("body", existing["body"])
    update_data["variables"] = extract_variables(new_subject + " " + new_body)

    if update_data.get("is_default"):
        await db.templates.update_many(
            {"user_id": existing["user_id"], "_id": {"$ne": ObjectId(template_id)}},
            {"$set": {"is_default": False}}
        )

    await db.templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": update_data}
    )

    updated = await db.templates.find_one({"_id": ObjectId(template_id)})

    return TemplateResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        category=updated["category"],
        subject=updated["subject"],
        body=updated["body"],
        variables=updated.get("variables", []),
        is_default=updated.get("is_default", False),
        created_at=updated["created_at"]
    )


@router.delete("/templates/{template_id}")
async def delete_any_template(template_id: str, admin=Depends(get_admin_user)):
    """Delete any template (admin only)."""
    db = get_database()

    result = await db.templates.delete_one({"_id": ObjectId(template_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}


# ==================== GLOBAL RECIPIENTS ====================

@router.get("/recipients", response_model=List[RecipientResponse])
async def get_all_recipients(admin=Depends(get_admin_user)):
    """Get all recipients from all users (admin only)."""
    db = get_database()
    recipients = await db.recipients.find().to_list(1000)

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


@router.post("/recipients/user/{user_id}", response_model=RecipientResponse)
async def create_recipient_for_user(
    user_id: str,
    recipient: RecipientCreate,
    admin=Depends(get_admin_user)
):
    """Create a recipient for a specific user (admin only)."""
    db = get_database()

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_recipient = {
        "user_id": user_id,
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


@router.delete("/recipients/{recipient_id}")
async def delete_any_recipient(recipient_id: str, admin=Depends(get_admin_user)):
    """Delete any recipient (admin only)."""
    db = get_database()

    result = await db.recipients.delete_one({"_id": ObjectId(recipient_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipient not found")

    return {"message": "Recipient deleted successfully"}


# ==================== BULK OPERATIONS ====================

@router.post("/templates/bulk-create")
async def bulk_create_templates(
    template: TemplateCreate,
    admin=Depends(get_admin_user)
):
    """Create the same template for all users (admin only)."""
    db = get_database()

    users = await db.users.find().to_list(1000)
    variables = extract_variables(template.subject + " " + template.body)

    templates_to_insert = []
    for user in users:
        new_template = {
            "user_id": str(user["_id"]),
            "name": template.name,
            "category": template.category.value,
            "subject": template.subject,
            "body": template.body,
            "variables": variables,
            "is_default": False,
            "created_at": datetime.utcnow()
        }
        templates_to_insert.append(new_template)

    if templates_to_insert:
        await db.templates.insert_many(templates_to_insert)

    return {"message": f"Template created for {len(templates_to_insert)} users"}


@router.post("/recipients/bulk-create")
async def bulk_create_recipients(
    recipient: RecipientCreate,
    admin=Depends(get_admin_user)
):
    """Create the same recipient for all users (admin only)."""
    db = get_database()

    users = await db.users.find().to_list(1000)

    recipients_to_insert = []
    for user in users:
        new_recipient = {
            "user_id": str(user["_id"]),
            "name": recipient.name,
            "email": recipient.email,
            "type": recipient.type.value,
            "is_default": recipient.is_default,
            "created_at": datetime.utcnow()
        }
        recipients_to_insert.append(new_recipient)

    if recipients_to_insert:
        await db.recipients.insert_many(recipients_to_insert)

    return {"message": f"Recipient created for {len(recipients_to_insert)} users"}
