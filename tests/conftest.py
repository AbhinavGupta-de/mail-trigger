import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from datetime import datetime
from bson import ObjectId

# Set test environment variables before importing app
import os
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "email_trigger_test"
os.environ["ADMIN_EMAILS"] = "admin@test.com"

from app.main import app
from app.database import db, get_database
from app.auth.dependencies import get_current_user, get_admin_user

# Store current mock user for dependency override
_current_mock_user = None
_mock_db_instance = None


async def mock_get_current_user():
    """Mock dependency that returns the current mock user."""
    if _current_mock_user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _current_mock_user


async def mock_get_admin_user():
    """Mock dependency that returns admin user."""
    if _current_mock_user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not _current_mock_user.get("is_admin", False):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return _current_mock_user


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Create a mock MongoDB database."""
    global _mock_db_instance
    mock_client = AsyncMongoMockClient()
    db.client = mock_client
    _mock_db_instance = mock_client["email_trigger_test"]
    yield _mock_db_instance
    # Cleanup
    await mock_client["email_trigger_test"].users.drop()
    await mock_client["email_trigger_test"].templates.drop()
    await mock_client["email_trigger_test"].recipients.drop()
    await mock_client["email_trigger_test"].email_logs.drop()


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
    global _current_mock_user
    _current_mock_user = None  # Reset for each test

    # Override auth dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_admin_user] = mock_get_admin_user

    with patch("app.database.get_database", return_value=mock_db):
        with TestClient(app) as c:
            yield c

    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(mock_db):
    """Create a test user in the database."""
    user_data = {
        "_id": ObjectId(),
        "email": "test@test.com",
        "name": "Test User",
        "google_id": "test-google-id",
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_expiry": None,
        "is_admin": False,
        "created_at": datetime.utcnow()
    }
    await mock_db.users.insert_one(user_data)
    return user_data


@pytest.fixture
async def admin_user(mock_db):
    """Create an admin user in the database."""
    user_data = {
        "_id": ObjectId(),
        "email": "admin@test.com",
        "name": "Admin User",
        "google_id": "admin-google-id",
        "access_token": "admin-access-token",
        "refresh_token": "admin-refresh-token",
        "token_expiry": None,
        "is_admin": True,
        "created_at": datetime.utcnow()
    }
    await mock_db.users.insert_one(user_data)
    return user_data


@pytest.fixture
async def test_template(mock_db, test_user):
    """Create a test template."""
    template_data = {
        "_id": ObjectId(),
        "user_id": str(test_user["_id"]),
        "name": "Test Template",
        "category": "leave",
        "subject": "Test Subject - {{date}}",
        "body": "Dear Sir, I {{name}} request...",
        "variables": ["date", "name"],
        "is_default": True,
        "created_at": datetime.utcnow()
    }
    await mock_db.templates.insert_one(template_data)
    return template_data


@pytest.fixture
async def test_recipient(mock_db, test_user):
    """Create a test recipient."""
    recipient_data = {
        "_id": ObjectId(),
        "user_id": str(test_user["_id"]),
        "name": "Test Warden",
        "email": "warden@test.com",
        "type": "to",
        "is_default": True,
        "created_at": datetime.utcnow()
    }
    await mock_db.recipients.insert_one(recipient_data)
    return recipient_data


def set_current_user(user_data):
    """Helper to set the current mock user for authentication."""
    global _current_mock_user
    _current_mock_user = user_data


def clear_current_user():
    """Helper to clear the current mock user."""
    global _current_mock_user
    _current_mock_user = None


@pytest.fixture
def auth_client(client, test_user):
    """Create a test client authenticated as a regular user."""
    set_current_user(test_user)
    yield client
    clear_current_user()


@pytest.fixture
def admin_client(client, admin_user):
    """Create a test client authenticated as an admin user."""
    set_current_user(admin_user)
    yield client
    clear_current_user()
