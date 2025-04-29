"""Tests for exe_builder module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

from teamschatgrab.exe_builder import ExeBuilder, build_exe


@pytest.fixture
def mock_pyinstaller():
    """Mock PyInstaller import."""
    pyinstaller_mock = mock.MagicMock()
    main_mock = mock.MagicMock()
    pyinstaller_mock.__main__ = main_mock
    
    with mock.patch.dict("sys.modules", {"PyInstaller": pyinstaller_mock}):
        yield main_mock


@pytest.fixture
def mock_exists():
    """Mock path exists method."""
    with mock.patch("pathlib.Path.exists", return_value=True):
        yield


@pytest.fixture
def test_base_path():
    """Create a test base path."""
    return Path("/test/path")


@pytest.fixture
def builder(test_base_path):
    """Create a test builder instance."""
    return ExeBuilder(base_path=test_base_path)


class TestExeBuilder:
    """Tests for ExeBuilder class."""

    def test_init(self, test_base_path):
        """Test initializing the builder."""
        builder = ExeBuilder(base_path=test_base_path)
        
        assert builder.base_path == test_base_path
        assert builder.dist_path == test_base_path / "dist"

    def test_build_windows_exe_missing_pyinstaller(self, builder, monkeypatch):
        """Test building when PyInstaller is not installed."""
        # Simulate PyInstaller not being installed
        monkeypatch.setitem(sys.modules, "PyInstaller.__main__", None)
        
        with pytest.raises(ImportError) as excinfo:
            builder.build_windows_exe()
        
        assert "PyInstaller is required" in str(excinfo.value)

    def test_build_windows_exe_missing_main_script(self, builder):
        """Test building when main script is not found."""
        with mock.patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as excinfo:
                builder.build_windows_exe()
            
            assert "Entry point not found" in str(excinfo.value)

    def test_build_windows_exe_success(self, builder, mock_pyinstaller, mock_exists):
        """Test successful Windows exe build."""
        # Mock the executable file check
        with mock.patch("pathlib.Path.exists", return_value=True):
            result = builder.build_windows_exe(
                name="TestApp", onefile=True, console=False
            )
            
            # Check the result
            assert result == builder.dist_path / "TestApp.exe"
            
            # Verify PyInstaller was called with correct args
            mock_pyinstaller.run.assert_called_once()
            args = mock_pyinstaller.run.call_args[0][0]
            
            assert str(builder.base_path / "main.py") in args
            assert "--name=TestApp" in args
            assert "--onefile" in args
            assert "--noconsole" in args
            assert any(arg.startswith("--add-data=") for arg in args)

    def test_build_windows_exe_build_fails(self, builder, mock_pyinstaller, mock_exists):
        """Test handling of build failure."""
        # Mock PyInstaller.run to raise an exception
        mock_pyinstaller.run.side_effect = RuntimeError("Build failed")
        
        with pytest.raises(RuntimeError) as excinfo:
            builder.build_windows_exe()
        
        assert "Failed to build executable" in str(excinfo.value)

    def test_build_windows_exe_executable_not_found(self, builder, mock_pyinstaller):
        """Test handling when executable file is not created."""
        # We need to make sure exists() is patched correctly to mimic our scenario
        # First call to exists() should return True (for main.py and LICENSE check)
        # Second call to exists() should return False (for the exe file check)
        with mock.patch("pathlib.Path.exists", side_effect=[True, True, False]):
            with pytest.raises(RuntimeError) as excinfo:
                builder.build_windows_exe(name="MissingExe")
            
            assert "Expected executable not found" in str(excinfo.value)
            assert "MissingExe.exe" in str(excinfo.value)


class TestBuildExe:
    """Tests for the build_exe function."""

    @mock.patch("teamschatgrab.exe_builder.ExeBuilder")
    def test_build_exe_windows(self, mock_builder_class, monkeypatch):
        """Test the build_exe function on Windows."""
        # Mock sys.platform to simulate Windows
        monkeypatch.setattr(sys, "platform", "win32")
        
        # Create mock builder instance
        mock_builder = mock.MagicMock()
        mock_builder_class.return_value = mock_builder
        
        # Mock return value of build_windows_exe
        expected_path = Path("/test/path/dist/TestApp.exe")
        mock_builder.build_windows_exe.return_value = expected_path
        
        # Call the function
        result = build_exe("TestApp", onefile=True, console=False)
        
        # Check results
        assert result == expected_path
        mock_builder.build_windows_exe.assert_called_once_with(
            "TestApp", True, False
        )

    @mock.patch("teamschatgrab.exe_builder.ExeBuilder")
    def test_build_exe_unsupported_platform(self, mock_builder_class, monkeypatch):
        """Test the build_exe function on an unsupported platform."""
        # Mock sys.platform to simulate Linux
        monkeypatch.setattr(sys, "platform", "linux")
        
        with pytest.raises(NotImplementedError) as excinfo:
            build_exe()
        
        assert "not yet supported" in str(excinfo.value)
        assert "linux" in str(excinfo.value)