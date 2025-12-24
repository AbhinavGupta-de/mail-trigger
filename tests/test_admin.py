import pytest
from unittest.mock import patch
from bson import ObjectId


class TestAdminAPI:
    """Test cases for admin API endpoints."""

    @pytest.mark.asyncio
    async def test_get_users_unauthenticated(self, client):
        """Test that unauthenticated users cannot access admin endpoints."""
        response = client.get("/api/admin/users")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_users_non_admin(self, auth_client, mock_db):
        """Test that non-admin users cannot access admin endpoints."""
        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = auth_client.get("/api/admin/users")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_users_admin(self, admin_client, mock_db, test_user):
        """Test that admin users can get all users."""
        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.get("/api/admin/users")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2  # admin + test user

    @pytest.mark.asyncio
    async def test_delete_user_admin(self, admin_client, mock_db, test_user):
        """Test that admin can delete a user."""
        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.delete(f"/api/admin/users/{test_user['_id']}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_self_forbidden(self, admin_client, mock_db, admin_user):
        """Test that admin cannot delete themselves."""
        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.delete(f"/api/admin/users/{admin_user['_id']}")
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_all_templates_admin(self, admin_client, mock_db, test_template):
        """Test that admin can get all templates."""
        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.get("/api/admin/templates")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_bulk_create_template(self, admin_client, mock_db, test_user):
        """Test bulk creating templates for all users."""
        template_data = {
            "name": "Bulk Template",
            "category": "other",
            "subject": "Bulk Subject",
            "body": "Bulk body content",
            "is_default": False
        }

        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.post("/api/admin/templates/bulk-create", json=template_data)
            assert response.status_code == 200
            data = response.json()
            assert "Template created for" in data["message"]

    @pytest.mark.asyncio
    async def test_bulk_create_recipient(self, admin_client, mock_db, test_user):
        """Test bulk creating recipients for all users."""
        recipient_data = {
            "name": "Bulk Warden",
            "email": "bulk.warden@test.com",
            "type": "to",
            "is_default": True
        }

        with patch("app.routes.admin.get_database", return_value=mock_db):
            response = admin_client.post("/api/admin/recipients/bulk-create", json=recipient_data)
            assert response.status_code == 200
            data = response.json()
            assert "Recipient created for" in data["message"]
