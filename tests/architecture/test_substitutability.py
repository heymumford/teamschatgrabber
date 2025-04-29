"""Tests to verify components can be substituted without affecting core logic.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from unittest import mock
from pathlib import Path

from teamschatgrab.app import TeamsChatGrabber
from teamschatgrab.api import ChatType
from teamschatgrab.storage import StorageFormat


class MockUI:
    """Mock UI implementation to substitute for TerminalUI."""

    def __init__(self, **kwargs):
        self.log_messages = []
        self.prompts = []
        self.selections = []
        self.confirmations = []
        self.next_input = "mock input"
        self.next_selection = 0
        self.next_confirmation = True

    def log(self, message, level=None):
        self.log_messages.append((message, level))

    def info(self, message):
        self.log(message, "info")

    def warning(self, message):
        self.log(message, "warning")

    def error(self, message):
        self.log(message, "error")

    def success(self, message):
        self.log(message, "success")

    def prompt(self, message, default=None):
        self.prompts.append((message, default))
        return self.next_input

    def select_option(self, message, options, descriptions=None):
        self.selections.append((message, options, descriptions))
        return self.next_selection

    def confirm(self, message, default=False):
        self.confirmations.append((message, default))
        return self.next_confirmation

    def progress(self, total, description):
        return {"total": total, "current": 0, "description": description}

    def start_progress(self, progress):
        pass

    def update_progress(self, progress, advance=1):
        progress["current"] += advance

    def stop_progress(self, progress):
        pass

    def display_table(self, headers, rows, title=None):
        pass


class MockTeamsApi:
    """Mock API implementation to substitute for TeamsApi."""

    def __init__(self, token):
        self.token = token
        self.chats_data = [
            {
                "id": "chat123",
                "displayName": "Test Chat",
                "isGroup": False,
                "participants": [
                    {"displayName": "User 1"},
                    {"displayName": "User 2"},
                ],
            }
        ]
        self.messages_data = [
            {
                "id": "msg1",
                "createdDateTime": "2023-01-01T12:00:00Z",
                "sender": {"user": {"displayName": "User 1"}},
                "body": {"content": "Hello from mock!"},
            }
        ]

    def get_chats(self):
        return self.chats_data

    def get_channels(self, team_id):
        return []

    def get_messages(self, chat_id, chat_type, limit=None, before_date=None):
        return self.messages_data

    def get_all_messages(self, chat_id, chat_type, limit=None):
        for msg in self.messages_data:
            yield msg


class MockStorage:
    """Mock storage implementation to substitute for TeamsStorage."""

    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path("/mock/path")
        self.saved_messages = []
        self.saved_attachments = []

    def create_chat_directory(self, chat_name, chat_id, chat_type):
        return self.base_path / chat_type.value / f"{chat_name}_{chat_id[-8:]}"

    def save_messages(self, messages, chat_dir, format=StorageFormat.JSON):
        self.saved_messages.append((messages, chat_dir, format))
        return chat_dir / f"messages_mock.{format.value}"

    def save_attachment(self, attachment_data, filename, chat_dir):
        self.saved_attachments.append((attachment_data, filename, chat_dir))
        return chat_dir / "attachments" / filename


def test_app_uses_ui_interface():
    """Test that app interacts with UI through interfaces."""
    # Mock platform info to avoid filesystem operations
    with mock.patch(
        "teamschatgrab.app.get_platform_info"
    ) as mock_platform_info, mock.patch(
        "teamschatgrab.storage.TeamsStorage._ensure_dir"
    ), mock.patch(
        "os.path.exists", return_value=True
    ):
        # Configure mocks - platform_type needs to have a value attribute
        from teamschatgrab.platform_detection import PlatformType

        mock_platform_info.return_value = {
            "platform": PlatformType.MACOS,
            "teams_data_path": "/mock/teams/path",
        }

        # Create app with real UI but mocked environment
        app = TeamsChatGrabber(output_dir=None, use_rich_ui=True)

        # Mock the app's UI class with a spy to track calls
        mock_ui = mock.MagicMock()
        app.ui = mock_ui

        # Run the operation that uses the UI
        app.check_environment()

        # Verify app used UI through interface
        assert mock_ui.info.called
        assert mock_ui.success.called


def test_app_uses_api_interface():
    """Test that app interacts with API through interfaces."""
    # Mock the necessary components to avoid file system operations
    with mock.patch("teamschatgrab.storage.TeamsStorage._ensure_dir"), mock.patch(
        "teamschatgrab.app.get_platform_info"
    ):
        # Create app with minimal initialization
        app = TeamsChatGrabber(use_rich_ui=False)

        # Create mock API and inject it
        mock_api = mock.MagicMock()
        mock_api.get_chats.return_value = [
            {"id": "chat123", "displayName": "Test Chat", "isGroup": False}
        ]
        app.api = mock_api

        # Set up a mock UI to prevent terminal output
        app.ui = mock.MagicMock()

        # Run the operation that uses the API
        app.list_chats()

        # Verify app used API through interface
        assert mock_api.get_chats.called


def test_app_uses_storage_interface():
    """Test that app uses storage through interface."""
    # Mock the necessary components to avoid file system operations
    with mock.patch("teamschatgrab.storage.TeamsStorage._ensure_dir"), mock.patch(
        "teamschatgrab.app.get_platform_info"
    ):
        # Create app with minimal initialization
        app = TeamsChatGrabber(use_rich_ui=False)

        # Mock the storage and inject it
        mock_storage = mock.MagicMock()
        mock_storage.create_chat_directory.return_value = Path("/mock/chat/dir")
        mock_storage.save_messages.return_value = Path("/mock/chat/dir/messages.json")
        app.storage = mock_storage

        # Mock API for test data
        app.api = mock.MagicMock()
        app.api.get_all_messages.return_value = [
            {"id": "msg1", "createdDateTime": "2023-01-01T12:00:00Z"}
        ]

        # Mock UI to prevent output
        app.ui = mock.MagicMock()

        # Run the operation that uses storage
        chat = {"id": "chat123", "displayName": "Test Chat"}
        chat_type = ChatType.DIRECT
        config = {"format": StorageFormat.JSON}

        app.download_chat(chat, chat_type, config)

        # Verify app used storage through interface
        assert mock_storage.create_chat_directory.called
        assert mock_storage.save_messages.called
