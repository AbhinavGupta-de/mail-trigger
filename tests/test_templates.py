import pytest
from unittest.mock import patch
from bson import ObjectId


class TestTemplatesAPI:
    """Test cases for templates API endpoints."""

    @pytest.mark.asyncio
    async def test_get_templates_unauthenticated(self, client):
        """Test that unauthenticated users cannot access templates."""
        response = client.get("/api/templates")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_templates_empty(self, auth_client, mock_db):
        """Test getting templates when none exist."""
        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.get("/api/templates")
            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_templates_with_data(self, auth_client, mock_db, test_template):
        """Test getting templates with existing data."""
        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.get("/api/templates")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Test Template"
            assert data[0]["category"] == "leave"

    @pytest.mark.asyncio
    async def test_create_template(self, auth_client, mock_db):
        """Test creating a new template."""
        template_data = {
            "name": "New Template",
            "category": "request",
            "subject": "Request - {{date}}",
            "body": "Dear Sir, {{name}} requests...",
            "is_default": False
        }

        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.post("/api/templates", json=template_data)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Template"
            assert data["category"] == "request"
            assert "date" in data["variables"]
            assert "name" in data["variables"]

    @pytest.mark.asyncio
    async def test_create_template_extracts_variables(self, auth_client, mock_db):
        """Test that template creation correctly extracts variables."""
        template_data = {
            "name": "Variable Test",
            "category": "other",
            "subject": "{{var1}} - {{var2}}",
            "body": "Content with {{var3}} and {{var1}}",
            "is_default": False
        }

        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.post("/api/templates", json=template_data)
            assert response.status_code == 200
            data = response.json()
            # Should have unique variables
            assert set(data["variables"]) == {"var1", "var2", "var3"}

    @pytest.mark.asyncio
    async def test_update_template(self, auth_client, mock_db, test_template):
        """Test updating an existing template."""
        update_data = {
            "name": "Updated Template",
            "subject": "New Subject - {{new_var}}"
        }

        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.put(
                f"/api/templates/{test_template['_id']}",
                json=update_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Template"
            assert "new_var" in data["variables"]

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, auth_client, mock_db):
        """Test updating a non-existent template."""
        fake_id = str(ObjectId())

        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.put(
                f"/api/templates/{fake_id}",
                json={"name": "Updated"}
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template(self, auth_client, mock_db, test_template):
        """Test deleting a template."""
        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.delete(f"/api/templates/{test_template['_id']}")
            assert response.status_code == 200

            # Verify it's deleted
            response = auth_client.get("/api/templates")
            assert len(response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, auth_client, mock_db):
        """Test deleting a non-existent template."""
        fake_id = str(ObjectId())

        with patch("app.routes.templates.get_database", return_value=mock_db):
            response = auth_client.delete(f"/api/templates/{fake_id}")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_default_template_unsets_others(self, auth_client, mock_db, test_template):
        """Test that setting a template as default unsets other defaults."""
        # Create another template
        new_template = {
            "name": "Another Template",
            "category": "other",
            "subject": "Subject",
            "body": "Body",
            "is_default": True
        }

        with patch("app.routes.templates.get_database", return_value=mock_db):
            # Create new default template
            response = auth_client.post("/api/templates", json=new_template)
            assert response.status_code == 200
            new_data = response.json()
            assert new_data["is_default"] == True

            # Check that original template is no longer default
            response = auth_client.get(f"/api/templates/{test_template['_id']}")
            assert response.status_code == 200
            original_data = response.json()
            assert original_data["is_default"] == False
