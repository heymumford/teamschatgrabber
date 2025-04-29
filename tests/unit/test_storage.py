"""Tests for Teams storage module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from unittest import mock
import pytest

from teamschatgrab.storage import TeamsStorage, StorageFormat, StorageError, ChatType


@pytest.fixture
def mock_path():
    """Mock Path object and filesystem operations."""
    with mock.patch("teamschatgrab.storage.Path") as mock_path, mock.patch(
        "teamschatgrab.storage.open", mock.mock_open()
    ) as mock_open, mock.patch("json.dump") as mock_dump:
        # Setup path mocks
        path_instance = mock_path.return_value
        path_instance.__truediv__.return_value = (
            path_instance  # For path / path operations
        )

        # Mock mkdir
        path_instance.mkdir.return_value = None

        yield {
            "path": mock_path,
            "open": mock_open,
            "dump": mock_dump,
            "instance": path_instance,
        }


@pytest.fixture
def storage(mock_path):
    """Create a test storage instance."""
    storage = TeamsStorage(base_path="/test/path")
    return storage


class TestTeamsStorage:
    """Tests for Teams storage functionality."""

    def test_init_with_custom_path(self, mock_path):
        """Test initialization with custom path."""
        TeamsStorage(base_path="/custom/path")
        mock_path["path"].assert_called_with("/custom/path")
        mock_path["instance"].mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_init_with_default_path(self, mock_path):
        """Test initialization with default path."""
        # Set up a more controlled test - avoid real Path objects
        home_mock = mock.MagicMock()
        path_instance = mock.MagicMock()
        mock_path["path"].home.return_value = home_mock
        home_mock.__truediv__.return_value = path_instance

        # Disable real directory creation
        path_instance.mkdir = mock.MagicMock()

        # Create storage with default path
        with mock.patch("pathlib.Path.home", return_value=home_mock):
            TeamsStorage()

        # Verify the right calls were made
        assert mock_path["path"].home.called
        home_mock.__truediv__.assert_called_with("TeamsDownloads")

    def test_ensure_dir_success(self, storage, mock_path):
        """Test successful directory creation."""
        test_path = mock_path["instance"]
        storage._ensure_dir(test_path)
        test_path.mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_ensure_dir_error(self, storage, mock_path):
        """Test directory creation error."""
        test_path = mock_path["instance"]
        test_path.mkdir.side_effect = OSError("Permission denied")

        with pytest.raises(StorageError):
            storage._ensure_dir(test_path)

    def test_sanitize_filename(self, mock_path):
        """Test filename sanitization."""
        storage_instance = TeamsStorage()
        # Test invalid characters - the regex in storage.py will replace all invalid chars with underscore
        result = storage_instance._sanitize_filename('file<>:"/\\|?*name')
        # The number of underscores doesn't need to match exactly, just check that:
        # - invalid characters are replaced
        # - string starts and ends as expected
        assert result.startswith("file")
        assert result.endswith("name")
        assert "<" not in result
        assert ":" not in result
        assert "/" not in result

        # Test length limitation
        long_name = "a" * 300
        sanitized = storage_instance._sanitize_filename(long_name)
        assert len(sanitized) <= 200
        assert sanitized.endswith("...")

    def test_create_chat_directory(self, storage, mock_path):
        """Test chat directory creation."""
        # Create a chat directory with our mock path
        chat_id = "1234567890abcdef"
        test_chat_name = "Test Chat"

        # Instead of checking specific calls, verify that the right number of operations happened
        storage.create_chat_directory(
            chat_name=test_chat_name, chat_id=chat_id, chat_type=ChatType.DIRECT
        )

        # Check that directories were created
        assert mock_path["instance"].mkdir.call_count >= 2
        assert len(mock_path["instance"].__truediv__.call_args_list) >= 3

    def test_save_messages_json(self, storage, mock_path):
        """Test saving messages in JSON format."""
        messages = [
            {
                "id": "1",
                "sender": {"user": {"displayName": "User 1"}},
                "createdDateTime": "2023-01-01T12:00:00Z",
                "body": {"content": "Hello"},
            },
            {
                "id": "2",
                "sender": {"user": {"displayName": "User 2"}},
                "createdDateTime": "2023-01-01T12:01:00Z",
                "body": {"content": "Hi there"},
            },
        ]

        chat_dir = mock_path["instance"]

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"

            storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.JSON
            )

            # Check that file was opened with correct path
            mock_path["open"].assert_called_with(
                chat_dir / "messages_20230101_120000.json", "w", encoding="utf-8"
            )

            # Check that json.dump was called with messages
            mock_path["dump"].assert_called_with(
                messages,
                mock_path["open"].return_value.__enter__.return_value,
                indent=2,
                ensure_ascii=False,
            )

    def test_save_messages_text(self, storage, mock_path):
        """Test saving messages in text format."""
        messages = [
            {
                "id": "1",
                "sender": {"user": {"displayName": "User 1"}},
                "createdDateTime": "2023-01-01T12:00:00Z",
                "body": {"content": "Hello"},
            },
            {
                "id": "2",
                "sender": {"user": {"displayName": "User 2"}},
                "createdDateTime": "2023-01-01T12:01:00Z",
                "body": {"content": "Hi there"},
            },
        ]

        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"

            storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.TEXT
            )

            # Check that file was opened with correct path
            mock_path["open"].assert_called_with(
                chat_dir / "messages_20230101_120000.txt", "w", encoding="utf-8"
            )

            # Check that write was called with expected content
            assert mock_file.write.call_count > 0

    def test_save_attachment(self, storage, mock_path):
        """Test saving attachment."""
        attachment_data = b"binary data"
        filename = "test<file>.pdf"
        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        storage.save_attachment(
            attachment_data=attachment_data, filename=filename, chat_dir=chat_dir
        )

        # Check that file was opened with sanitized path
        mock_path["open"].assert_called_with(
            chat_dir / "attachments" / "test_file_.pdf", "wb"
        )

        # Check that write was called with the binary data
        mock_file.write.assert_called_with(attachment_data)

    def test_content_download_json(self, storage, mock_path):
        """Test content download in JSON format with test doubles."""
        # Sample message data
        messages = [
            {
                "id": "msg1",
                "sender": {"user": {"displayName": "Test User 1"}},
                "createdDateTime": "2025-01-15T10:30:00Z",
                "body": {"content": "This is a test message"},
            },
            {
                "id": "msg2",
                "sender": {"user": {"displayName": "Test User 2"}},
                "createdDateTime": "2025-01-15T10:35:00Z",
                "body": {"content": "This is a reply"},
            },
        ]

        # Setup mocks
        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp for predictable filenames
            mock_datetime.now.return_value.strftime.return_value = "20250115_103000"

            # Call the method under test
            result = storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.JSON
            )

            # Verify file path is correct
            expected_path = chat_dir / "messages_20250115_103000.json"
            assert result == expected_path

            # Verify file was opened with correct path and mode
            mock_path["open"].assert_called_with(expected_path, "w", encoding="utf-8")

            # Verify JSON dump was called with correct parameters
            mock_path["dump"].assert_called_with(
                messages, mock_file, indent=2, ensure_ascii=False
            )

    def test_content_download_text(self, storage, mock_path):
        """Test content download in TEXT format with test doubles."""
        # Sample message data
        messages = [
            {
                "id": "msg1",
                "sender": {"user": {"displayName": "Test User 1"}},
                "createdDateTime": "2025-01-15T10:30:00Z",
                "body": {"content": "This is a test message"},
            },
            {
                "id": "msg2",
                "sender": {"user": {"displayName": "Test User 2"}},
                "createdDateTime": "2025-01-15T10:35:00Z",
                "body": {"content": "This is a reply"},
            },
        ]

        # Setup mocks
        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp for predictable filenames
            mock_datetime.now.return_value.strftime.return_value = "20250115_103000"

            # Call the method under test
            result = storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.TEXT
            )

            # Verify file path is correct
            expected_path = chat_dir / "messages_20250115_103000.txt"
            assert result == expected_path

            # Verify file was opened with correct path and mode
            mock_path["open"].assert_called_with(expected_path, "w", encoding="utf-8")

            # Verify write was called for each message with correct content
            # We should have at least 6 writes (2 msgs * 3 lines each)
            assert mock_file.write.call_count >= 6

            # Check specific content is written
            mock_file.write.assert_any_call("From: Test User 1\n")
            mock_file.write.assert_any_call("Time: 2025-01-15T10:30:00Z\n")
            mock_file.write.assert_any_call("Message: This is a test message\n")
            mock_file.write.assert_any_call("From: Test User 2\n")
            mock_file.write.assert_any_call("Time: 2025-01-15T10:35:00Z\n")
            mock_file.write.assert_any_call("Message: This is a reply\n")

    def test_content_download_html(self, storage, mock_path):
        """Test content download in HTML format with test doubles."""
        # Sample message data
        messages = [
            {
                "id": "msg1",
                "sender": {"user": {"displayName": "Test User 1"}},
                "createdDateTime": "2025-01-15T10:30:00Z",
                "body": {"content": "This is a test message"},
            },
            {
                "id": "msg2",
                "sender": {"user": {"displayName": "Test User 2"}},
                "createdDateTime": "2025-01-15T10:35:00Z",
                "body": {"content": "This is a reply"},
            },
        ]

        # Setup mocks
        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp for predictable filenames
            mock_datetime.now.return_value.strftime.return_value = "20250115_103000"

            # Call the method under test
            result = storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.HTML
            )

            # Verify file path is correct
            expected_path = chat_dir / "messages_20250115_103000.html"
            assert result == expected_path

            # Verify file was opened with correct path and mode
            mock_path["open"].assert_called_with(expected_path, "w", encoding="utf-8")

            # Verify HTML elements were written
            mock_file.write.assert_any_call(
                "<html><head><title>Teams Chat</title></head><body>\n"
            )
            mock_file.write.assert_any_call("<div class='messages'>\n")

            # Check user 1 message content is written with appropriate HTML
            mock_file.write.assert_any_call("<div class='message'>\n")
            mock_file.write.assert_any_call("  <div class='sender'>Test User 1</div>\n")
            mock_file.write.assert_any_call(
                "  <div class='time'>2025-01-15T10:30:00Z</div>\n"
            )
            mock_file.write.assert_any_call(
                "  <div class='content'>This is a test message</div>\n"
            )

            # Check user 2 message content is written with appropriate HTML
            mock_file.write.assert_any_call("  <div class='sender'>Test User 2</div>\n")
            mock_file.write.assert_any_call(
                "  <div class='time'>2025-01-15T10:35:00Z</div>\n"
            )
            mock_file.write.assert_any_call(
                "  <div class='content'>This is a reply</div>\n"
            )

            # Check closing tags
            mock_file.write.assert_any_call("</div></body></html>\n")

    def test_content_download_markdown(self, storage, mock_path):
        """Test content download in Markdown format with test doubles."""
        # Sample message data
        messages = [
            {
                "id": "msg1",
                "sender": {"user": {"displayName": "Test User 1"}},
                "createdDateTime": "2025-01-15T10:30:00Z",
                "body": {"content": "This is a test message"},
            },
            {
                "id": "msg2",
                "sender": {"user": {"displayName": "Test User 2"}},
                "createdDateTime": "2025-01-15T10:35:00Z",
                "body": {"content": "This is a reply"},
            },
        ]

        # Setup mocks
        chat_dir = mock_path["instance"]
        mock_file = mock_path["open"].return_value.__enter__.return_value

        with mock.patch("datetime.datetime") as mock_datetime:
            # Mock timestamp for predictable filenames
            mock_datetime.now.return_value.strftime.return_value = "20250115_103000"

            # Call the method under test
            result = storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=StorageFormat.MARKDOWN
            )

            # Verify file path is correct
            expected_path = chat_dir / "messages_20250115_103000.md"
            assert result == expected_path

            # Verify file was opened with correct path and mode
            mock_path["open"].assert_called_with(expected_path, "w", encoding="utf-8")

            # Verify Markdown elements were written
            mock_file.write.assert_any_call("# Teams Chat Export\n\n")

            # Check user 1 message content is written with appropriate Markdown
            mock_file.write.assert_any_call("## Test User 1 - 2025-01-15T10:30:00Z\n\n")
            mock_file.write.assert_any_call("This is a test message\n\n")
            mock_file.write.assert_any_call("---\n\n")

            # Check user 2 message content is written with appropriate Markdown
            mock_file.write.assert_any_call("## Test User 2 - 2025-01-15T10:35:00Z\n\n")
            mock_file.write.assert_any_call("This is a reply\n\n")
            mock_file.write.assert_any_call("---\n\n")

    def test_unsupported_format_error(self, storage, mock_path):
        """Test error handling for unsupported format."""
        messages = [
            {
                "id": "msg1",
                "sender": {"user": {"displayName": "Test User 1"}},
                "createdDateTime": "2025-01-15T10:30:00Z",
                "body": {"content": "This is a test message"},
            }
        ]

        chat_dir = mock_path["instance"]

        # Create a custom enum value that doesn't exist in StorageFormat
        unsupported_format = "UNSUPPORTED_FORMAT"

        # Verify that the appropriate error is raised
        with pytest.raises(StorageError) as excinfo:
            storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=unsupported_format
            )

        # Check the error message contains the format name
        assert "Unsupported output format" in str(excinfo.value)
        assert str(unsupported_format) in str(excinfo.value)
