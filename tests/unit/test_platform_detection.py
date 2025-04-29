"""Tests for platform detection module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import os
from unittest import mock

import pytest

from teamschatgrab.platform_detection import (
    PlatformType,
    detect_platform,
    get_teams_data_path,
    get_platform_info,
)


@pytest.fixture
def mock_windows():
    """Mock Windows environment."""
    with mock.patch("platform.system", return_value="Windows"), mock.patch(
        "os.path.expandvars",
        return_value=r"C:\Users\testuser\AppData\Roaming\Microsoft\Teams",
    ):
        yield


@pytest.fixture
def mock_macos():
    """Mock macOS environment."""
    with mock.patch("platform.system", return_value="Darwin"), mock.patch(
        "os.path.expanduser",
        return_value="/Users/testuser/Library/Application Support/Microsoft/Teams",
    ):
        yield


@pytest.fixture
def mock_wsl():
    """Mock WSL environment."""
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "platform.uname", return_value=mock.Mock(release="5.10.16.3-microsoft-standard")
    ), mock.patch.dict(os.environ, {"USER": "testuser"}):
        yield


@pytest.fixture
def mock_linux():
    """Mock Linux environment."""
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "platform.uname", return_value=mock.Mock(release="5.15.0-generic")
    ):
        yield


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_detect_windows(self, mock_windows):
        """Test Windows platform detection."""
        assert detect_platform() == PlatformType.WINDOWS

    def test_detect_macos(self, mock_macos):
        """Test macOS platform detection."""
        assert detect_platform() == PlatformType.MACOS

    def test_detect_wsl(self, mock_wsl):
        """Test WSL platform detection."""
        assert detect_platform() == PlatformType.WSL

    def test_detect_linux(self, mock_linux):
        """Test Linux platform detection."""
        assert detect_platform() == PlatformType.LINUX

    def test_get_teams_data_path_windows(self, mock_windows):
        """Test getting Teams data path on Windows."""
        assert (
            get_teams_data_path()
            == r"C:\Users\testuser\AppData\Roaming\Microsoft\Teams"
        )

    def test_get_teams_data_path_macos(self, mock_macos):
        """Test getting Teams data path on macOS."""
        assert (
            get_teams_data_path()
            == "/Users/testuser/Library/Application Support/Microsoft/Teams"
        )

    def test_get_teams_data_path_wsl(self, mock_wsl):
        """Test getting Teams data path on WSL."""
        assert (
            get_teams_data_path()
            == "/mnt/c/Users/testuser/AppData/Roaming/Microsoft/Teams"
        )

    def test_get_teams_data_path_linux(self, mock_linux):
        """Test getting Teams data path on Linux (should be None)."""
        assert get_teams_data_path() is None

    def test_get_platform_info_includes_required_keys(self, mock_macos):
        """Test that platform info contains all required keys."""
        info = get_platform_info()
        required_keys = [
            "platform",
            "system",
            "release",
            "version",
            "python_version",
            "teams_data_path",
        ]
        for key in required_keys:
            assert key in info
