from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.database import get_database
from app.services.gmail import send_email, substitute_variables
from app.models.email_log import EmailLogResponse

router = APIRouter(prefix="/api/email", tags=["email"])


class SendEmailRequest(BaseModel):
    template_id: Optional[str] = None
    to: List[EmailStr]
    cc: List[EmailStr] = []
    subject: str
    body: str
    variables: Dict[str, str] = {}


class SendWithTemplateRequest(BaseModel):
    template_id: str
    to: Optional[List[EmailStr]] = None  # If not provided, use default recipients
    cc: Optional[List[EmailStr]] = None  # If not provided, use default CC
    variables: Dict[str, str] = {}


@router.post("/send")
async def send_custom_email(
    request: SendEmailRequest,
    user=Depends(get_current_user)
):
    """Send a custom email (without using a template)."""
    # Substitute variables
    subject = substitute_variables(request.subject, request.variables, user)
    body = substitute_variables(request.body, request.variables, user)

    result = await send_email(
        user=user,
        to=request.to,
        cc=request.cc,
        subject=subject,
        body=body,
        template_id=request.template_id
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/send-template")
async def send_template_email(
    request: SendWithTemplateRequest,
    user=Depends(get_current_user)
):
    """Send an email using a template."""
    db = get_database()

    # Get the template
    template = await db.templates.find_one({
        "_id": ObjectId(request.template_id),
        "user_id": str(user["_id"])
    })

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Get recipients
    if request.to is None:
        # Use default TO recipients
        default_to = await db.recipients.find({
            "user_id": str(user["_id"]),
            "type": "to",
            "is_default": True
        }).to_list(100)
        to_emails = [r["email"] for r in default_to]
    else:
        to_emails = request.to

    if request.cc is None:
        # Use default CC recipients
        default_cc = await db.recipients.find({
            "user_id": str(user["_id"]),
            "type": "cc",
            "is_default": True
        }).to_list(100)
        cc_emails = [r["email"] for r in default_cc]
    else:
        cc_emails = request.cc

    if not to_emails:
        raise HTTPException(
            status_code=400,
            detail="No recipients specified. Please add recipients or set default recipients."
        )

    # Substitute variables
    subject = substitute_variables(template["subject"], request.variables, user)
    body = substitute_variables(template["body"], request.variables, user)

    result = await send_email(
        user=user,
        to=to_emails,
        cc=cc_emails,
        subject=subject,
        body=body,
        template_id=request.template_id
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.get("/logs", response_model=List[EmailLogResponse])
async def get_email_logs(user=Depends(get_current_user)):
    """Get email sending history for current user."""
    db = get_database()
    logs = await db.email_logs.find(
        {"user_id": str(user["_id"])}
    ).sort("sent_at", -1).to_list(100)

    return [
        EmailLogResponse(
            id=str(log["_id"]),
            template_id=log.get("template_id"),
            to=log["to"],
            cc=log.get("cc", []),
            subject=log["subject"],
            status=log["status"],
            sent_at=log["sent_at"]
        )
        for log in logs
    ]


@router.get("/preview-template/{template_id}")
async def preview_template(
    template_id: str,
    user=Depends(get_current_user)
):
    """Preview a template with variables filled in."""
    db = get_database()

    template = await db.templates.find_one({
        "_id": ObjectId(template_id),
        "user_id": str(user["_id"])
    })

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Get default recipients
    default_to = await db.recipients.find({
        "user_id": str(user["_id"]),
        "type": "to",
        "is_default": True
    }).to_list(100)

    default_cc = await db.recipients.find({
        "user_id": str(user["_id"]),
        "type": "cc",
        "is_default": True
    }).to_list(100)

    # Preview with auto-fill variables only
    preview_subject = substitute_variables(template["subject"], {}, user)
    preview_body = substitute_variables(template["body"], {}, user)

    return {
        "template_name": template["name"],
        "subject": preview_subject,
        "body": preview_body,
        "variables": template.get("variables", []),
        "default_to": [{"name": r["name"], "email": r["email"]} for r in default_to],
        "default_cc": [{"name": r["name"], "email": r["email"]} for r in default_cc]
    }
