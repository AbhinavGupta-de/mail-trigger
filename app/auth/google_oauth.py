from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import get_settings
import json

settings = get_settings()


def create_oauth_flow(redirect_uri: str = None) -> Flow:
    """Create Google OAuth flow."""
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{settings.app_url}/auth/callback"],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=settings.google_scopes,
        redirect_uri=redirect_uri or f"{settings.app_url}/auth/callback"
    )

    return flow


def get_authorization_url() -> tuple[str, str]:
    """Get Google OAuth authorization URL and state."""
    flow = create_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return authorization_url, state


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for tokens."""
    flow = create_oauth_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "scopes": list(credentials.scopes) if credentials.scopes else []
    }


def refresh_access_token(refresh_token: str) -> dict:
    """Refresh access token using refresh token."""
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )

    credentials.refresh(Request())

    return {
        "access_token": credentials.token,
        "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None
    }


def get_credentials_from_tokens(access_token: str, refresh_token: str) -> Credentials:
    """Create Credentials object from tokens."""
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )
