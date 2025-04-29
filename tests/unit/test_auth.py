"""
Tests for Teams authentication module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from unittest import mock

import pytest

from teamschatgrab.auth import (
    find_token_db_path,
    get_current_user_info,
    validate_token,
    refresh_token,
)
from teamschatgrab.platform_detection import PlatformType


@pytest.fixture
def mock_windows_teams_data():
    """Mock Windows Teams data path."""
    with mock.patch(
        "teamschatgrab.auth.detect_platform", return_value=PlatformType.WINDOWS
    ), mock.patch(
        "teamschatgrab.auth.get_teams_data_path",
        return_value=r"C:\Users\testuser\AppData\Roaming\Microsoft\Teams",
    ), mock.patch(
        "os.path.exists", return_value=True
    ), mock.patch(
        "os.path.join",
        return_value=r"C:\Users\testuser\AppData\Roaming\Microsoft\Teams\Local Storage\leveldb",
    ):
        yield


@pytest.fixture
def mock_macos_teams_data():
    """Mock macOS Teams data path."""
    with mock.patch(
        "teamschatgrab.auth.detect_platform", return_value=PlatformType.MACOS
    ), mock.patch(
        "teamschatgrab.auth.get_teams_data_path",
        return_value="/Users/testuser/Library/Application Support/Microsoft/Teams",
    ), mock.patch(
        "os.path.exists", return_value=True
    ), mock.patch(
        "os.path.join", side_effect=lambda *args: "/".join(args)
    ):
        yield


@pytest.fixture
def mock_no_teams_data():
    """Mock missing Teams data path."""
    with mock.patch(
        "teamschatgrab.auth.get_teams_data_path", return_value=None
    ), mock.patch("os.path.exists", return_value=False):
        yield


class TestTeamsAuth:
    """Tests for Teams authentication functions."""

    def test_find_token_db_path_windows(self, mock_windows_teams_data):
        """Test finding token DB path on Windows."""
        result = find_token_db_path()
        assert (
            result
            == r"C:\Users\testuser\AppData\Roaming\Microsoft\Teams\Local Storage\leveldb"
        )

    def test_find_token_db_path_macos(self, mock_macos_teams_data):
        """Test finding token DB path on macOS."""
        result = find_token_db_path()
        assert "Local Storage/leveldb" in result

    def test_find_token_db_path_no_teams(self, mock_no_teams_data):
        """Test finding token DB path when Teams is not installed."""
        result = find_token_db_path()
        assert result is None

    def test_get_current_user_info_success(self, mock_windows_teams_data):
        """Test getting current user info successfully."""
        result = get_current_user_info()
        assert result is not None
        assert "user_id" in result
        assert "email" in result
        assert "name" in result
        assert "token" in result

    def test_get_current_user_info_no_teams(self, mock_no_teams_data):
        """Test getting user info when Teams is not installed."""
        result = get_current_user_info()
        assert result is None

    def test_validate_token_invalid(self):
        """Test validating an invalid token."""
        is_valid, error = validate_token("placeholder_token")
        assert not is_valid
        assert error is not None

    def test_validate_token_empty(self):
        """Test validating an empty token."""
        is_valid, error = validate_token("")
        assert not is_valid
        assert error is not None

    def test_validate_token_valid(self):
        """Test validating a valid token."""
        is_valid, error = validate_token("valid_token_123")
        assert is_valid
        assert error is None

    def test_refresh_token_success(self):
        """Test successfully refreshing a token."""
        new_token = refresh_token("valid_token_123")
        assert new_token is not None
        assert new_token != "valid_token_123"

    def test_refresh_token_failure(self):
        """Test failing to refresh an invalid token."""
        new_token = refresh_token("placeholder_token")
        assert new_token is None
