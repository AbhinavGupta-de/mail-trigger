from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from datetime import datetime
import re

from app.auth.dependencies import get_current_user
from app.database import get_database
from app.models.template import TemplateCreate, TemplateUpdate, TemplateResponse

router = APIRouter(prefix="/api/templates", tags=["templates"])


def extract_variables(text: str) -> List[str]:
    """Extract template variables like {{variable}} from text."""
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, text)
    return list(set(matches))


@router.get("", response_model=List[TemplateResponse])
async def get_templates(user=Depends(get_current_user)):
    """Get all templates for current user."""
    db = get_database()
    templates = await db.templates.find({"user_id": str(user["_id"])}).to_list(100)

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


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, user=Depends(get_current_user)):
    """Get a specific template."""
    db = get_database()
    template = await db.templates.find_one({
        "_id": ObjectId(template_id),
        "user_id": str(user["_id"])
    })

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse(
        id=str(template["_id"]),
        name=template["name"],
        category=template["category"],
        subject=template["subject"],
        body=template["body"],
        variables=template.get("variables", []),
        is_default=template.get("is_default", False),
        created_at=template["created_at"]
    )


@router.post("", response_model=TemplateResponse)
async def create_template(template: TemplateCreate, user=Depends(get_current_user)):
    """Create a new template."""
    db = get_database()

    # Extract variables from subject and body
    variables = extract_variables(template.subject + " " + template.body)

    new_template = {
        "user_id": str(user["_id"]),
        "name": template.name,
        "category": template.category.value,
        "subject": template.subject,
        "body": template.body,
        "variables": variables,
        "is_default": template.is_default,
        "created_at": datetime.utcnow()
    }

    # If this is set as default, unset other defaults
    if template.is_default:
        await db.templates.update_many(
            {"user_id": str(user["_id"])},
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


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template: TemplateUpdate,
    user=Depends(get_current_user)
):
    """Update a template."""
    db = get_database()

    existing = await db.templates.find_one({
        "_id": ObjectId(template_id),
        "user_id": str(user["_id"])
    })

    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = template.model_dump(exclude_unset=True)

    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].value

    # Re-extract variables if subject or body changed
    new_subject = update_data.get("subject", existing["subject"])
    new_body = update_data.get("body", existing["body"])
    update_data["variables"] = extract_variables(new_subject + " " + new_body)

    # If setting as default, unset others
    if update_data.get("is_default"):
        await db.templates.update_many(
            {"user_id": str(user["_id"]), "_id": {"$ne": ObjectId(template_id)}},
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


@router.delete("/{template_id}")
async def delete_template(template_id: str, user=Depends(get_current_user)):
    """Delete a template."""
    db = get_database()

    result = await db.templates.delete_one({
        "_id": ObjectId(template_id),
        "user_id": str(user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}
