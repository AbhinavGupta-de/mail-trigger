from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
from datetime import datetime

from app.auth.google_oauth import get_authorization_url, exchange_code_for_tokens
from app.database import get_database
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/login")
async def login(request: Request):
    """Redirect to Google OAuth login."""
    authorization_url, state = get_authorization_url()
    request.session["oauth_state"] = state
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def callback(request: Request, code: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    try:
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(code)

        # Get user info from Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            user_info = response.json()

        db = get_database()

        # Check if user exists
        existing_user = await db.users.find_one({"google_id": user_info["id"]})

        # Check if user is admin
        is_admin = user_info["email"].lower() in settings.get_admin_emails()

        if existing_user:
            # Update tokens and admin status
            await db.users.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "access_token": tokens["access_token"],
                        "refresh_token": tokens.get("refresh_token", existing_user.get("refresh_token")),
                        "token_expiry": tokens.get("token_expiry"),
                        "is_admin": is_admin
                    }
                }
            )
            user_id = str(existing_user["_id"])
        else:
            # Create new user
            new_user = {
                "email": user_info["email"],
                "name": user_info.get("name", user_info["email"]),
                "google_id": user_info["id"],
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "token_expiry": tokens.get("token_expiry"),
                "is_admin": is_admin,
                "created_at": datetime.utcnow()
            }
            result = await db.users.insert_one(new_user)
            user_id = str(result.inserted_id)

            # Create default templates for new user
            await create_default_templates(db, user_id)

        # Set session
        request.session["user_id"] = user_id

        return RedirectResponse(url="/dashboard", status_code=302)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/logout")
async def logout(request: Request):
    """Logout user."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


async def create_default_templates(db, user_id: str):
    """Create default email templates for new user."""
    default_templates = [
        {
            "user_id": user_id,
            "name": "Leave Application",
            "category": "leave",
            "subject": "Leave Application - {{date}}",
            "body": """Dear Sir/Madam,

I, {{name}}, am writing to request leave from {{from_date}} to {{to_date}}.

Reason: {{reason}}

I request you to kindly grant me leave for the mentioned period.

Thank you.

Regards,
{{name}}""",
            "variables": ["name", "date", "from_date", "to_date", "reason"],
            "is_default": True,
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_id,
            "name": "Late Entry Request",
            "category": "request",
            "subject": "Request for Late Entry - {{date}}",
            "body": """Dear Warden,

I, {{name}}, request permission for late entry on {{date}}.

Reason: {{reason}}

I will ensure this does not become a regular occurrence.

Regards,
{{name}}""",
            "variables": ["name", "date", "reason"],
            "is_default": False,
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_id,
            "name": "General Complaint",
            "category": "complaint",
            "subject": "Complaint - {{subject}}",
            "body": """Dear Warden,

I am writing to bring to your attention the following matter:

{{details}}

I request you to kindly look into this matter.

Thank you.

Regards,
{{name}}""",
            "variables": ["name", "subject", "details"],
            "is_default": False,
            "created_at": datetime.utcnow()
        }
    ]

    await db.templates.insert_many(default_templates)
