from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from typing import List, Optional
from datetime import datetime
import re

from app.config import get_settings
from app.database import get_database

settings = get_settings()


async def get_user_credentials(user: dict) -> Credentials:
    """Get and refresh user's Google credentials."""
    credentials = Credentials(
        token=user["access_token"],
        refresh_token=user["refresh_token"],
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        # Update tokens in database
        db = get_database()
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "access_token": credentials.token,
                    "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None
                }
            }
        )

    return credentials


def substitute_variables(text: str, variables: dict, user: dict) -> str:
    """Replace template variables with actual values."""
    # Auto-fill variables
    auto_fill = {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Merge with user-provided variables (user-provided takes precedence)
    all_vars = {**auto_fill, **variables}

    # Replace {{variable}} patterns
    def replace_var(match):
        var_name = match.group(1)
        return all_vars.get(var_name, match.group(0))  # Keep original if not found

    return re.sub(r'\{\{(\w+)\}\}', replace_var, text)


def create_message(
    sender: str,
    to: List[str],
    cc: List[str],
    subject: str,
    body: str
) -> dict:
    """Create an email message for sending via Gmail API."""
    message = MIMEMultipart()
    message["from"] = sender
    message["to"] = ", ".join(to)
    if cc:
        message["cc"] = ", ".join(cc)
    message["subject"] = subject

    # Attach body as plain text
    message.attach(MIMEText(body, "plain"))

    # Encode to base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    return {"raw": raw_message}


async def send_email(
    user: dict,
    to: List[str],
    cc: List[str],
    subject: str,
    body: str,
    template_id: Optional[str] = None
) -> dict:
    """Send an email using the Gmail API."""
    try:
        credentials = await get_user_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        # Create the message
        message = create_message(
            sender=user["email"],
            to=to,
            cc=cc,
            subject=subject,
            body=body
        )

        # Send the message
        result = service.users().messages().send(
            userId="me",
            body=message
        ).execute()

        # Log the email
        db = get_database()
        await db.email_logs.insert_one({
            "user_id": str(user["_id"]),
            "template_id": template_id,
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "status": "sent",
            "message_id": result.get("id"),
            "sent_at": datetime.utcnow()
        })

        return {
            "success": True,
            "message_id": result.get("id"),
            "message": "Email sent successfully"
        }

    except Exception as e:
        # Log failed attempt
        db = get_database()
        await db.email_logs.insert_one({
            "user_id": str(user["_id"]),
            "template_id": template_id,
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "status": "failed",
            "error": str(e),
            "sent_at": datetime.utcnow()
        })

        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to send email: {str(e)}"
        }
