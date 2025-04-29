"""
Tests for Teams API client.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import datetime
from unittest import mock
import pytest
import requests

from teamschatgrab.api import TeamsApi, TeamsApiError, TeamsAuthError, ChatType


@pytest.fixture
def mock_session():
    """Mock requests session."""
    with mock.patch("teamschatgrab.api.requests.Session") as mock_session:
        session_instance = mock_session.return_value
        session_instance.request.return_value = mock.Mock(
            status_code=200, json=mock.Mock(return_value={"data": "test_data"})
        )
        yield session_instance


@pytest.fixture
def mock_session_auth_error():
    """Mock requests session with auth error."""
    with mock.patch("teamschatgrab.api.requests.Session") as mock_session:
        session_instance = mock_session.return_value
        response = mock.Mock(status_code=401)
        response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        session_instance.request.return_value = response
        yield session_instance


@pytest.fixture
def mock_session_api_error():
    """Mock requests session with API error."""
    with mock.patch("teamschatgrab.api.requests.Session") as mock_session:
        session_instance = mock_session.return_value
        response = mock.Mock(status_code=500)
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        session_instance.request.return_value = response
        yield session_instance


@pytest.fixture
def api_client(mock_session):
    """Create a test API client."""
    return TeamsApi(token="test_token")


class TestTeamsApi:
    """Tests for Teams API client."""

    def test_init_sets_headers(self, api_client, mock_session):
        """Test that init sets the correct headers."""
        headers = mock_session.headers.update.call_args[0][0]
        assert "Authorization" in headers
        assert "Bearer test_token" in headers["Authorization"]
        assert "Content-Type" in headers
        assert "User-Agent" in headers

    def test_make_request_success(self, api_client, mock_session):
        """Test successful API request."""
        result = api_client._make_request("GET", "test_endpoint")
        assert result == {"data": "test_data"}
        mock_session.request.assert_called_once_with(
            method="GET",
            url=f"{TeamsApi.BASE_URL}/test_endpoint",
            params=None,
            json=None,
        )

    def test_make_request_auth_error(self, mock_session_auth_error):
        """Test API request with auth error."""
        api_client = TeamsApi(token="invalid_token")
        with pytest.raises(TeamsAuthError):
            api_client._make_request("GET", "test_endpoint")

    def test_make_request_api_error(self, mock_session_api_error):
        """Test API request with API error."""
        api_client = TeamsApi(token="test_token")
        with pytest.raises(TeamsApiError):
            api_client._make_request("GET", "test_endpoint")

    def test_get_chats(self, api_client, mock_session):
        """Test getting chats."""
        result = api_client.get_chats()
        assert result == {"data": "test_data"}
        mock_session.request.assert_called_with(
            method="GET", url=f"{TeamsApi.BASE_URL}/chats", params=None, json=None
        )

    def test_get_channels(self, api_client, mock_session):
        """Test getting channels."""
        result = api_client.get_channels(team_id="team123")
        assert result == {"data": "test_data"}
        mock_session.request.assert_called_with(
            method="GET",
            url=f"{TeamsApi.BASE_URL}/teams/team123/channels",
            params=None,
            json=None,
        )

    def test_get_messages_direct_chat(self, api_client, mock_session):
        """Test getting messages from direct chat."""
        result = api_client.get_messages(
            chat_id="chat123", chat_type=ChatType.DIRECT, limit=50
        )
        assert result == {"data": "test_data"}
        mock_session.request.assert_called_with(
            method="GET",
            url=f"{TeamsApi.BASE_URL}/chats/chat123/messages",
            params={"limit": "50"},
            json=None,
        )

    def test_get_messages_channel(self, api_client, mock_session):
        """Test getting messages from channel."""
        test_date = datetime.datetime(2023, 1, 1)
        result = api_client.get_messages(
            chat_id="channel123",
            chat_type=ChatType.CHANNEL,
            limit=50,
            before_date=test_date,
        )
        assert result == {"data": "test_data"}
        mock_session.request.assert_called_with(
            method="GET",
            url=f"{TeamsApi.BASE_URL}/channels/channel123/messages",
            params={"limit": "50", "before": test_date.isoformat()},
            json=None,
        )

    def test_get_all_messages(self, api_client, mock_session):
        """Test paginated message fetching."""
        # Setup mock to return different responses for pagination testing
        mock_session.request.side_effect = [
            mock.Mock(
                status_code=200,
                json=mock.Mock(
                    return_value={
                        "messages": [
                            {"id": "msg1", "createdDateTime": "2023-01-02T00:00:00"},
                            {"id": "msg2", "createdDateTime": "2023-01-01T00:00:00"},
                        ]
                    }
                ),
            ),
            mock.Mock(status_code=200, json=mock.Mock(return_value={"messages": []})),
        ]

        # Test the generator
        messages = list(
            api_client.get_all_messages(
                chat_id="chat123", chat_type=ChatType.DIRECT, limit=10
            )
        )

        assert len(messages) == 2
        assert messages[0]["id"] == "msg1"
        assert messages[1]["id"] == "msg2"
