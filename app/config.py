from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Google OAuth
    google_client_id: str
    google_client_secret: str

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "email_trigger"

    # App
    secret_key: str
    app_url: str = "http://localhost:8000"

    # Admin emails (comma-separated in .env)
    admin_emails: str = ""

    # Google OAuth Scopes
    google_scopes: list = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.send"
    ]

    class Config:
        env_file = ".env"

    def get_admin_emails(self) -> List[str]:
        """Parse comma-separated admin emails."""
        if not self.admin_emails:
            return []
        return [e.strip().lower() for e in self.admin_emails.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
