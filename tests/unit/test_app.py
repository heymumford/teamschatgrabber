"""Tests for main application module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from pathlib import Path
from unittest import mock

import pytest

from teamschatgrab.app import TeamsChatGrabber, create_app
from teamschatgrab.api import ChatType, TeamsApiError
from teamschatgrab.auth import TeamsAuthError
from teamschatgrab.storage import StorageFormat
from teamschatgrab.platform_detection import PlatformType


@pytest.fixture
def mock_ui():
    """Mock terminal UI."""
    with mock.patch("teamschatgrab.app.TerminalUI") as mock_ui_class:
        ui_instance = mock_ui_class.return_value

        # Mock UI methods
        ui_instance.info = mock.Mock()
        ui_instance.success = mock.Mock()
        ui_instance.warning = mock.Mock()
        ui_instance.error = mock.Mock()
        ui_instance.prompt = mock.Mock(return_value="test input")
        ui_instance.confirm = mock.Mock(return_value=True)
        ui_instance.select_option = mock.Mock(return_value=0)

        # Mock progress methods
        progress_obj = {"progress": mock.Mock(), "task": "task1"}
        ui_instance.progress = mock.Mock(return_value=progress_obj)
        ui_instance.start_progress = mock.Mock()
        ui_instance.update_progress = mock.Mock()
        ui_instance.stop_progress = mock.Mock()

        yield ui_instance


@pytest.fixture
def mock_platform():
    """Mock platform detection."""
    with mock.patch("teamschatgrab.app.get_platform_info") as mock_platform_info:
        mock_platform_info.return_value = {
            "platform": PlatformType.MACOS,
            "system": "Darwin",
            "release": "21.6.0",
            "version": "Darwin Kernel Version 21.6.0",
            "python_version": "3.9.0",
            "teams_data_path": "/Users/testuser/Library/Application Support/Microsoft/Teams",
        }

        with mock.patch("os.path.exists", return_value=True):
            yield mock_platform_info


@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with mock.patch(
        "teamschatgrab.app.get_current_user_info"
    ) as mock_user_info, mock.patch(
        "teamschatgrab.app.validate_token"
    ) as mock_validate:
        mock_user_info.return_value = {
            "user_id": "user123",
            "email": "user@example.com",
            "name": "Test User",
            "token": "valid_token_123",
        }

        mock_validate.return_value = (True, None)

        yield {"user_info": mock_user_info, "validate": mock_validate}


@pytest.fixture
def mock_api():
    """Mock Teams API."""
    with mock.patch("teamschatgrab.app.TeamsApi") as mock_api_class:
        api_instance = mock_api_class.return_value

        # Mock API methods
        api_instance.get_chats = mock.Mock(
            return_value=[
                {
                    "id": "chat123",
                    "displayName": "Test Chat 1",
                    "isGroup": False,
                    "participants": [
                        {"displayName": "User 1"},
                        {"displayName": "User 2"},
                    ],
                },
                {
                    "id": "chat456",
                    "displayName": "Test Group",
                    "isGroup": True,
                    "participants": [
                        {"displayName": "User 1"},
                        {"displayName": "User 2"},
                        {"displayName": "User 3"},
                    ],
                },
            ]
        )

        # Mock messages generator
        def mock_get_all_messages(*args, **kwargs):
            messages = [
                {
                    "id": "msg1",
                    "createdDateTime": "2023-01-01T12:00:00Z",
                    "sender": {"user": {"displayName": "User 1"}},
                    "body": {"content": "Hello"},
                },
                {
                    "id": "msg2",
                    "createdDateTime": "2023-01-01T12:01:00Z",
                    "sender": {"user": {"displayName": "User 2"}},
                    "body": {"content": "Hi there"},
                },
            ]
            for msg in messages:
                yield msg

        api_instance.get_all_messages = mock_get_all_messages

        yield api_instance


@pytest.fixture
def mock_storage():
    """Mock storage."""
    with mock.patch("teamschatgrab.app.TeamsStorage") as mock_storage_class:
        storage_instance = mock_storage_class.return_value

        # Mock storage methods
        storage_instance.create_chat_directory = mock.Mock(
            return_value=Path("/test/output/direct/Test_Chat_1_chat123")
        )

        storage_instance.save_messages = mock.Mock(
            return_value=Path(
                "/test/output/direct/Test_Chat_1_chat123/messages_20230101_120000.json"
            )
        )

        yield storage_instance


@pytest.fixture
def app(mock_ui, mock_platform, mock_storage):
    """Create a test app instance with mocks."""
    app = TeamsChatGrabber(output_dir="/test/output", use_rich_ui=True)
    app.api = mock.Mock()  # Will be replaced in tests that need API mocking
    return app


class TestTeamsChatGrabber:
    """Tests for Teams chat grabber application."""

    def test_init(self, mock_ui, mock_platform, mock_storage):
        """Test initialization."""
        app = TeamsChatGrabber(output_dir="/test/output", use_rich_ui=True)
        assert app.ui is mock_ui
        assert app.platform_info == mock_platform.return_value
        assert app.storage is mock_storage
        assert app.api is None
        assert app.user_info is None

    def test_check_environment_success(self, app):
        """Test successful environment check."""
        # Mock os.path.exists to return True
        with mock.patch("os.path.exists", return_value=True):
            result = app.check_environment()

            assert result is True
            app.ui.success.assert_called_with("Environment check passed")

    def test_check_environment_no_teams_path(self, app):
        """Test environment check with missing Teams path."""
        # Override platform info
        app.platform_info["teams_data_path"] = None

        result = app.check_environment()

        assert result is False
        app.ui.error.assert_called_with("Microsoft Teams data path not found")

    def test_authenticate_success(self, app, mock_auth):
        """Test successful authentication."""
        result = app.authenticate()

        assert result is True
        assert app.user_info == mock_auth["user_info"].return_value
        assert app.ui.success.called

        # Check if TeamsApi was created
        assert app.api is not None

    def test_authenticate_no_user(self, app, mock_auth):
        """Test authentication with no user."""
        mock_auth["user_info"].return_value = None

        result = app.authenticate()

        assert result is False
        assert app.ui.error.called

    def test_authenticate_invalid_token(self, app, mock_auth):
        """Test authentication with invalid token."""
        mock_auth["validate"].return_value = (False, "Invalid token")

        result = app.authenticate()

        assert result is False
        assert app.ui.error.called

    def test_authenticate_error(self, app, mock_auth):
        """Test authentication error."""
        mock_auth["user_info"].side_effect = TeamsAuthError("Auth failed")

        result = app.authenticate()

        assert result is False
        assert app.ui.error.called

    def test_list_chats_success(self, app, mock_api):
        """Test successful listing of chats."""
        app.api = mock_api

        chats, channels = app.list_chats()

        assert len(chats) == 2
        assert len(channels) == 0
        assert app.ui.success.called

    def test_list_chats_not_authenticated(self, app):
        """Test listing chats when not authenticated."""
        app.api = None

        chats, channels = app.list_chats()

        assert len(chats) == 0
        assert len(channels) == 0
        assert app.ui.error.called

    def test_list_chats_api_error(self, app, mock_api):
        """Test API error when listing chats."""
        app.api = mock_api
        mock_api.get_chats.side_effect = TeamsApiError("API error")

        chats, channels = app.list_chats()

        assert len(chats) == 0
        assert len(channels) == 0
        assert app.ui.error.called

    def test_select_chat(self, app, mock_api):
        """Test chat selection."""
        chats = mock_api.get_chats()
        channels = []

        app.ui.select_option.return_value = 0  # Select first chat

        selected, chat_type = app.select_chat(chats, channels)

        assert selected is chats[0]
        assert chat_type == ChatType.DIRECT
        assert app.ui.select_option.called

    def test_select_chat_group(self, app, mock_api):
        """Test group chat selection."""
        chats = mock_api.get_chats()
        channels = []

        app.ui.select_option.return_value = 1  # Select second chat (group)

        selected, chat_type = app.select_chat(chats, channels)

        assert selected is chats[1]
        assert chat_type == ChatType.GROUP
        assert app.ui.select_option.called

    def test_select_chat_no_chats(self, app):
        """Test chat selection with no chats."""
        selected, chat_type = app.select_chat([], [])

        assert selected is None
        assert app.ui.error.called

    def test_configure_download(self, app):
        """Test download configuration."""
        app.ui.select_option.return_value = 0  # JSON format
        app.ui.prompt.side_effect = ["100", "", ""]  # limit, date_from, date_to
        app.ui.confirm.return_value = True  # Use date range

        config = app.configure_download()

        assert config["format"] == StorageFormat.JSON
        assert config["limit"] == 100
        assert "date_from" in config
        assert "date_to" in config

    def test_download_chat_success(self, app, mock_api, mock_storage):
        """Test successful chat download."""
        app.api = mock_api

        chat = {"id": "chat123", "displayName": "Test Chat 1", "isGroup": False}

        config = {"format": StorageFormat.JSON, "limit": 10}

        result = app.download_chat(chat, ChatType.DIRECT, config)

        assert result is not None
        assert app.ui.success.called
        assert mock_storage.create_chat_directory.called
        assert mock_storage.save_messages.called

    def test_download_chat_not_authenticated(self, app):
        """Test downloading chat when not authenticated."""
        app.api = None

        chat = {"id": "chat123", "displayName": "Test Chat"}
        config = {"format": StorageFormat.JSON}

        result = app.download_chat(chat, ChatType.DIRECT, config)

        assert result is None
        assert app.ui.error.called

    def test_download_chat_api_error(self, app, mock_api, mock_storage):
        """Test API error during chat download."""
        app.api = mock_api

        chat = {"id": "chat123", "displayName": "Test Chat"}
        config = {"format": StorageFormat.JSON}

        # Make get_all_messages raise an exception
        def mock_error_generator(*args, **kwargs):
            raise TeamsApiError("API error")
            yield {}  # Never reached

        mock_api.get_all_messages = mock_error_generator

        result = app.download_chat(chat, ChatType.DIRECT, config)

        assert result is None
        assert app.ui.error.called

    def test_run_success(self, app, mock_auth, mock_api, mock_storage):
        """Test successful complete run."""
        # Setup app
        app.check_environment = mock.Mock(return_value=True)
        app.authenticate = mock.Mock(return_value=True)
        app.list_chats = mock.Mock(return_value=(mock_api.get_chats(), []))

        # Mock chat selection
        chats = mock_api.get_chats()
        app.select_chat = mock.Mock(return_value=(chats[0], ChatType.DIRECT))

        # Mock download configuration and chat download
        config = {"format": StorageFormat.JSON, "limit": 10}
        app.configure_download = mock.Mock(return_value=config)
        app.download_chat = mock.Mock(return_value=Path("/test/output/chat123"))

        result = app.run()

        assert result is True
        assert app.check_environment.called
        assert app.authenticate.called
        assert app.list_chats.called
        assert app.select_chat.called
        assert app.configure_download.called
        assert app.download_chat.called
        assert app.ui.success.called

    def test_run_environment_check_failed(self, app):
        """Test run with failed environment check."""
        app.check_environment = mock.Mock(return_value=False)

        result = app.run()

        assert result is False
        assert app.check_environment.called
        assert not app.ui.success.called

    def test_create_app(self, mock_ui, mock_platform, mock_storage):
        """Test app factory function."""
        app = create_app(output_dir="/custom/path", use_rich_ui=True)

        assert isinstance(app, TeamsChatGrabber)
        assert app.ui is mock_ui
