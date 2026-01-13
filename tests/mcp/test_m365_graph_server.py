#!/usr/bin/env python3
"""
M365 Graph MCP Server Integration Tests
========================================

Generated with CodeLlama 13B (local LLM - 99.3% cost savings)

Tests authentication, email operations, Teams operations, Calendar operations,
and error handling using pytest with mocked Microsoft Graph SDK.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add maia root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Dependency guard - skip if MCP library not installed
try:
    from claude.tools.mcp.m365_graph_server import M365GraphClient
    MCP_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    MCP_AVAILABLE = False

if not MCP_AVAILABLE:
    pytest.skip("MCP library not installed", allow_module_level=True)


@pytest.fixture
def mock_graph_client():
    """Mock Microsoft Graph SDK client"""
    with patch('claude.tools.mcp.m365_graph_server.GraphServiceClient') as mock:
        yield mock


@pytest.fixture
def mock_credential():
    """Mock Azure AD credential"""
    with patch('claude.tools.mcp.m365_graph_server.DeviceCodeCredential') as mock:
        yield mock


class TestM365GraphAuthentication:
    """Test Azure AD authentication"""

    @pytest.mark.asyncio
    async def test_device_code_auth(self, mock_credential, mock_graph_client):
        """Test device code flow authentication"""
        client = M365GraphClient(
            tenant_id="test-tenant",
            client_id="test-client",
            use_device_code=True
        )

        await client._ensure_authenticated()

        # Verify device code credential was created
        mock_credential.assert_called_once_with(
            tenant_id="test-tenant",
            client_id="test-client"
        )

    @pytest.mark.asyncio
    async def test_client_secret_auth(self, mock_graph_client):
        """Test client secret authentication"""
        with patch('claude.tools.mcp.m365_graph_server.ClientSecretCredential') as mock_secret:
            client = M365GraphClient(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret",
                use_device_code=False
            )

            await client._ensure_authenticated()

            # Verify client secret credential was created
            mock_secret.assert_called_once_with(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            )


class TestM365EmailOperations:
    """Test Outlook/Exchange email operations"""

    @pytest.mark.asyncio
    async def test_list_messages(self, mock_graph_client):
        """Test listing inbox messages"""
        # Mock response
        mock_messages = MagicMock()
        mock_messages.value = [
            MagicMock(
                id="msg1",
                subject="Test Email",
                from_=MagicMock(email_address=MagicMock(address="test@example.com")),
                received_date_time=datetime.now(),
                is_read=False,
                has_attachments=False,
                importance="normal",
                body_preview="Test body"
            )
        ]

        mock_graph_client.return_value.me.mail_folders.by_mail_folder_id.return_value.messages.get = AsyncMock(
            return_value=mock_messages
        )

        client = M365GraphClient(tenant_id="test", client_id="test")
        client._graph_client = mock_graph_client.return_value

        result = await client.list_messages(folder="inbox", top=10)

        assert len(result) == 1
        assert result[0]["subject"] == "Test Email"
        assert result[0]["from"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_send_email(self, mock_graph_client):
        """Test sending email"""
        mock_graph_client.return_value.me.send_mail.post = AsyncMock()

        client = M365GraphClient(tenant_id="test", client_id="test", read_only=False)
        client._graph_client = mock_graph_client.return_value

        result = await client.send_email(
            to_recipients=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body"
        )

        assert result["success"] is True
        assert "recipient@example.com" in result["recipients"]

    @pytest.mark.asyncio
    async def test_send_email_read_only_blocked(self, mock_graph_client):
        """Test email sending blocked in read-only mode"""
        client = M365GraphClient(tenant_id="test", client_id="test", read_only=True)

        result = await client.send_email(
            to_recipients=["test@example.com"],
            subject="Test",
            body="Body"
        )

        assert "error" in result
        assert result["blocked"] is True


class TestM365TeamsOperations:
    """Test Microsoft Teams operations"""

    @pytest.mark.asyncio
    async def test_list_teams(self, mock_graph_client):
        """Test listing joined Teams"""
        mock_teams = MagicMock()
        mock_teams.value = [
            MagicMock(
                id="team1",
                display_name="Test Team",
                description="Test Description",
                is_archived=False,
                web_url="https://teams.microsoft.com/test"
            )
        ]

        mock_graph_client.return_value.me.joined_teams.get = AsyncMock(
            return_value=mock_teams
        )

        client = M365GraphClient(tenant_id="test", client_id="test")
        client._graph_client = mock_graph_client.return_value

        result = await client.list_teams()

        assert len(result) == 1
        assert result[0]["display_name"] == "Test Team"

    @pytest.mark.asyncio
    async def test_send_teams_message(self, mock_graph_client):
        """Test sending message to Teams channel"""
        mock_message = MagicMock(
            id="msg1",
            created_date_time=datetime.now()
        )

        mock_graph_client.return_value.teams.by_team_id.return_value.channels.by_channel_id.return_value.messages.post = AsyncMock(
            return_value=mock_message
        )

        client = M365GraphClient(tenant_id="test", client_id="test", read_only=False)
        client._graph_client = mock_graph_client.return_value

        result = await client.send_teams_message(
            team_id="team1",
            channel_id="channel1",
            message="Test message"
        )

        assert result["success"] is True
        assert result["message_id"] == "msg1"


class TestM365CalendarOperations:
    """Test Calendar operations"""

    @pytest.mark.asyncio
    async def test_list_calendar_events(self, mock_graph_client):
        """Test listing calendar events"""
        mock_events = MagicMock()
        mock_events.value = [
            MagicMock(
                id="event1",
                subject="Test Meeting",
                start=MagicMock(date_time="2025-10-01T09:00:00"),
                end=MagicMock(date_time="2025-10-01T10:00:00"),
                location=MagicMock(display_name="Conference Room"),
                is_online_meeting=True,
                online_meeting_url="https://teams.microsoft.com/meeting",
                attendees=[]
            )
        ]

        mock_graph_client.return_value.me.calendar_view.get = AsyncMock(
            return_value=mock_events
        )

        client = M365GraphClient(tenant_id="test", client_id="test")
        client._graph_client = mock_graph_client.return_value

        result = await client.list_calendar_events(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )

        assert len(result) == 1
        assert result[0]["subject"] == "Test Meeting"
        assert result[0]["is_online_meeting"] is True

    @pytest.mark.asyncio
    async def test_create_meeting(self, mock_graph_client):
        """Test creating calendar meeting"""
        mock_event = MagicMock(
            id="event1",
            subject="Test Meeting",
            online_meeting_url="https://teams.microsoft.com/meeting"
        )

        mock_graph_client.return_value.me.events.post = AsyncMock(
            return_value=mock_event
        )

        client = M365GraphClient(tenant_id="test", client_id="test", read_only=False)
        client._graph_client = mock_graph_client.return_value

        result = await client.create_meeting(
            subject="Test Meeting",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            attendees=["attendee@example.com"],
            is_online_meeting=True
        )

        assert result["success"] is True
        assert result["subject"] == "Test Meeting"
        assert "online_meeting_url" in result


class TestM365ErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_authentication_failure(self, mock_credential):
        """Test handling of authentication failure"""
        mock_credential.side_effect = Exception("Auth failed")

        client = M365GraphClient(tenant_id="test", client_id="test")

        with pytest.raises(Exception):
            await client._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_graph_client):
        """Test handling of Graph API errors"""
        mock_graph_client.return_value.me.mail_folders.by_mail_folder_id.return_value.messages.get = AsyncMock(
            side_effect=Exception("API Error")
        )

        client = M365GraphClient(tenant_id="test", client_id="test")
        client._graph_client = mock_graph_client.return_value

        result = await client.list_messages()

        # Should return empty list on error, not crash
        assert result == []

    @pytest.mark.asyncio
    async def test_read_only_mode_enforcement(self, mock_graph_client):
        """Test that read-only mode blocks write operations"""
        client = M365GraphClient(tenant_id="test", client_id="test", read_only=True)

        # Test email send blocked
        email_result = await client.send_email(
            to_recipients=["test@example.com"],
            subject="Test",
            body="Body"
        )
        assert email_result["blocked"] is True

        # Test Teams message blocked
        teams_result = await client.send_teams_message(
            team_id="team1",
            channel_id="channel1",
            message="Test"
        )
        assert teams_result["blocked"] is True

        # Test meeting creation blocked
        meeting_result = await client.create_meeting(
            subject="Test",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            attendees=["test@example.com"]
        )
        assert meeting_result["blocked"] is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
