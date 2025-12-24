import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.services.gmail import substitute_variables, create_message


class TestGmailService:
    """Test cases for Gmail service functions."""

    def test_substitute_variables_auto_fill(self):
        """Test that auto-fill variables are substituted."""
        user = {"name": "John Doe", "email": "john@test.com"}
        text = "Hello {{name}}, your email is {{email}}"
        result = substitute_variables(text, {}, user)

        assert "John Doe" in result
        assert "john@test.com" in result

    def test_substitute_variables_date(self):
        """Test that date variable is substituted."""
        user = {"name": "Test", "email": "test@test.com"}
        text = "Today is {{date}}"
        result = substitute_variables(text, {}, user)

        # Date should be in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in result

    def test_substitute_variables_custom(self):
        """Test that custom variables are substituted."""
        user = {"name": "Test", "email": "test@test.com"}
        text = "Reason: {{reason}}, From: {{from_date}}"
        variables = {"reason": "Sick leave", "from_date": "2024-01-15"}
        result = substitute_variables(text, variables, user)

        assert "Sick leave" in result
        assert "2024-01-15" in result

    def test_substitute_variables_missing_kept(self):
        """Test that missing variables are kept as-is."""
        user = {"name": "Test", "email": "test@test.com"}
        text = "Unknown: {{unknown_var}}"
        result = substitute_variables(text, {}, user)

        assert "{{unknown_var}}" in result

    def test_substitute_variables_user_overrides_auto(self):
        """Test that user-provided variables override auto-fill."""
        user = {"name": "Auto Name", "email": "auto@test.com"}
        text = "Name: {{name}}"
        variables = {"name": "Custom Name"}
        result = substitute_variables(text, variables, user)

        assert "Custom Name" in result
        assert "Auto Name" not in result

    def test_create_message_basic(self):
        """Test creating a basic email message."""
        message = create_message(
            sender="sender@test.com",
            to=["recipient@test.com"],
            cc=[],
            subject="Test Subject",
            body="Test body content"
        )

        assert "raw" in message
        assert isinstance(message["raw"], str)
        # The raw message should be base64 encoded
        assert len(message["raw"]) > 0

    def test_create_message_with_cc(self):
        """Test creating an email message with CC."""
        message = create_message(
            sender="sender@test.com",
            to=["recipient@test.com"],
            cc=["cc1@test.com", "cc2@test.com"],
            subject="Test Subject",
            body="Test body"
        )

        assert "raw" in message

    def test_create_message_multiple_recipients(self):
        """Test creating an email with multiple recipients."""
        message = create_message(
            sender="sender@test.com",
            to=["r1@test.com", "r2@test.com", "r3@test.com"],
            cc=[],
            subject="Multi recipient test",
            body="Test body"
        )

        assert "raw" in message


class TestEmailSending:
    """Test cases for email sending functionality."""

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_db, test_user):
        """Test successful email sending."""
        from app.services.gmail import send_email

        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "msg123"}

        with patch("app.services.gmail.build", return_value=mock_service):
            with patch("app.services.gmail.get_user_credentials", new_callable=AsyncMock):
                with patch("app.services.gmail.get_database", return_value=mock_db):
                    result = await send_email(
                        user=test_user,
                        to=["recipient@test.com"],
                        cc=[],
                        subject="Test",
                        body="Test body"
                    )

                    assert result["success"] == True
                    assert result["message_id"] == "msg123"

    @pytest.mark.asyncio
    async def test_send_email_failure(self, mock_db, test_user):
        """Test email sending failure."""
        from app.services.gmail import send_email

        with patch("app.services.gmail.get_user_credentials", new_callable=AsyncMock) as mock_creds:
            mock_creds.side_effect = Exception("API Error")
            with patch("app.services.gmail.get_database", return_value=mock_db):
                result = await send_email(
                    user=test_user,
                    to=["recipient@test.com"],
                    cc=[],
                    subject="Test",
                    body="Test body"
                )

                assert result["success"] == False
                assert "error" in result
