import pytest
from unittest.mock import patch
from bson import ObjectId


class TestRecipientsAPI:
    """Test cases for recipients API endpoints."""

    @pytest.mark.asyncio
    async def test_get_recipients_unauthenticated(self, client):
        """Test that unauthenticated users cannot access recipients."""
        response = client.get("/api/recipients")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_recipients_empty(self, auth_client, mock_db):
        """Test getting recipients when none exist."""
        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.get("/api/recipients")
            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_recipients_with_data(self, auth_client, mock_db, test_recipient):
        """Test getting recipients with existing data."""
        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.get("/api/recipients")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Test Warden"
            assert data[0]["email"] == "warden@test.com"
            assert data[0]["type"] == "to"

    @pytest.mark.asyncio
    async def test_get_default_recipients(self, auth_client, mock_db, test_recipient):
        """Test getting default recipients."""
        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.get("/api/recipients/defaults")
            assert response.status_code == 200
            data = response.json()
            assert len(data["to"]) == 1
            assert data["to"][0]["email"] == "warden@test.com"
            assert len(data["cc"]) == 0

    @pytest.mark.asyncio
    async def test_create_recipient_to(self, auth_client, mock_db):
        """Test creating a TO recipient."""
        recipient_data = {
            "name": "New Warden",
            "email": "new.warden@test.com",
            "type": "to",
            "is_default": True
        }

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.post("/api/recipients", json=recipient_data)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Warden"
            assert data["type"] == "to"
            assert data["is_default"] == True

    @pytest.mark.asyncio
    async def test_create_recipient_cc(self, auth_client, mock_db):
        """Test creating a CC recipient."""
        recipient_data = {
            "name": "Parent",
            "email": "parent@test.com",
            "type": "cc",
            "is_default": True
        }

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.post("/api/recipients", json=recipient_data)
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "cc"

    @pytest.mark.asyncio
    async def test_create_recipient_invalid_email(self, auth_client, mock_db):
        """Test creating a recipient with invalid email."""
        recipient_data = {
            "name": "Invalid",
            "email": "not-an-email",
            "type": "to",
            "is_default": False
        }

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.post("/api/recipients", json=recipient_data)
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_recipient(self, auth_client, mock_db, test_recipient):
        """Test updating a recipient."""
        update_data = {
            "name": "Updated Warden",
            "email": "updated.warden@test.com"
        }

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.put(
                f"/api/recipients/{test_recipient['_id']}",
                json=update_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Warden"
            assert data["email"] == "updated.warden@test.com"

    @pytest.mark.asyncio
    async def test_update_recipient_not_found(self, auth_client, mock_db):
        """Test updating a non-existent recipient."""
        fake_id = str(ObjectId())

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.put(
                f"/api/recipients/{fake_id}",
                json={"name": "Updated"}
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_recipient(self, auth_client, mock_db, test_recipient):
        """Test deleting a recipient."""
        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.delete(f"/api/recipients/{test_recipient['_id']}")
            assert response.status_code == 200

            # Verify it's deleted
            response = auth_client.get("/api/recipients")
            assert len(response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_recipient_not_found(self, auth_client, mock_db):
        """Test deleting a non-existent recipient."""
        fake_id = str(ObjectId())

        with patch("app.routes.recipients.get_database", return_value=mock_db):
            response = auth_client.delete(f"/api/recipients/{fake_id}")
            assert response.status_code == 404
