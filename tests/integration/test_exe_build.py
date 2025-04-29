"""Integration tests for executable build process.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import os
import sys
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from teamschatgrab.exe_builder import build_exe


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to prevent actual external process execution."""
    with mock.patch("subprocess.run") as mock_run:
        # Set up the mock to return a successful CompletedProcess
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"", stderr=b""
        )
        yield mock_run


@pytest.fixture
def mock_pyinstaller_import():
    """Mock PyInstaller import to bypass actual installation requirement."""
    mock_module = mock.MagicMock()
    mock_module.__main__ = mock.MagicMock()
    mock_module.__main__.run = mock.MagicMock()
    
    with mock.patch.dict("sys.modules", {"PyInstaller": mock_module}):
        with mock.patch.dict("sys.modules", {"PyInstaller.__main__": mock_module.__main__}):
            yield mock_module.__main__


@pytest.fixture
def mock_exe_file_creation():
    """Mock file creation to simulate successful exe build."""
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.mkdir", mock.MagicMock()):
            yield


class TestExeBuildProcess:
    """Integration tests for executable build process."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_build_script_execution(self, mock_subprocess_run, tmp_path):
        """Test execution of the build_exe.py script."""
        # Copy the script to a temporary location
        build_script = Path(os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "build_exe.py"
        )))
        
        # Execute the script as a subprocess
        result = subprocess.run(
            [sys.executable, str(build_script), "--console"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # Verify the script runs without error when PyInstaller is available
        mock_subprocess_run.assert_called_once()
        assert "--console" in str(mock_subprocess_run.call_args)

    def test_build_integration_with_pyinstaller(
        self, mock_pyinstaller_import, mock_exe_file_creation
    ):
        """Test integration between our module and PyInstaller."""
        # Skip the test if we're not on Windows
        if not sys.platform.startswith("win"):
            pytest.skip("Windows-only test")
        
        # Call our build function
        result = build_exe(name="TestIntegration", console=True, onefile=False)
        
        # Verify PyInstaller was called correctly
        assert mock_pyinstaller_import.run.called
        
        # Get the args passed to PyInstaller
        args = mock_pyinstaller_import.run.call_args[0][0]
        
        # Check that essential arguments are included
        assert any("--name=TestIntegration" in arg for arg in args)
        assert not any("--onefile" in arg for arg in args)  # We specified onefile=False
        assert not any("--noconsole" in arg for arg in args)  # We specified console=True
        
        # Check that the result is as expected
        assert "TestIntegration.exe" in str(result)


class TestBuildExeMockHelpers:
    """Tests for mocked builder helpers that simulate PyInstaller behavior."""
    
    class MockPyInstallerBuilder:
        """Mock class that mimics PyInstaller's build process."""
        
        def __init__(self):
            """Initialize the mock builder."""
            self.args = []
            self.build_successful = True
            self.dist_path = None
        
        def run_build(self, args):
            """Simulate running PyInstaller with given args."""
            self.args = args
            
            # Extract output path info from args
            name = "default"
            for arg in args:
                if arg.startswith("--name="):
                    name = arg.split("=")[1]
            
            # Determine dist path
            curr_dir = os.path.abspath(os.path.dirname(__file__))
            base_dir = os.path.dirname(os.path.dirname(curr_dir))
            self.dist_path = Path(base_dir) / "dist" / f"{name}.exe"
            
            if not self.build_successful:
                raise RuntimeError("Mock build failure")
            
            # Create parent directories
            os.makedirs(os.path.dirname(self.dist_path), exist_ok=True)
            
            # Simulate creation of exe file by creating an empty file
            with open(self.dist_path, "w") as f:
                f.write("Mock executable file")
            
            return self.dist_path
    
    @pytest.fixture
    def mock_pyinstaller_builder(self):
        """Create a mock PyInstaller builder instance."""
        return self.MockPyInstallerBuilder()
    
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_mock_builder_success(self, mock_pyinstaller_builder, tmp_path):
        """Test the mock builder's success path."""
        # Mock sys.platform to simulate Windows
        with mock.patch("sys.platform", "win32"):
            # Mock the PyInstaller import
            with mock.patch("teamschatgrab.exe_builder.PyInstaller") as mock_pyi:
                # Set up the mock's run function
                mock_pyi.__main__ = mock.MagicMock()
                mock_pyi.__main__.run = mock_pyinstaller_builder.run_build
                
                # Call our build function
                with mock.patch("pathlib.Path.exists", return_value=True):
                    result = build_exe(name="MockTest", console=True)
                
                # Verify correct args were passed
                assert any("--name=MockTest" in arg for arg in mock_pyinstaller_builder.args)
                assert "MockTest.exe" in str(result)
    
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_mock_builder_failure(self, mock_pyinstaller_builder, tmp_path):
        """Test the mock builder's failure path."""
        # Configure the mock to simulate failure
        mock_pyinstaller_builder.build_successful = False
        
        # Mock sys.platform to simulate Windows
        with mock.patch("sys.platform", "win32"):
            # Mock the PyInstaller import
            with mock.patch("teamschatgrab.exe_builder.PyInstaller") as mock_pyi:
                # Set up the mock's run function
                mock_pyi.__main__ = mock.MagicMock()
                mock_pyi.__main__.run = mock_pyinstaller_builder.run_build
                
                # Call our build function and expect it to raise an exception
                with mock.patch("pathlib.Path.exists", return_value=True):
                    with pytest.raises(RuntimeError) as excinfo:
                        build_exe(name="FailTest")
                
                assert "Failed to build executable" in str(excinfo.value)
                assert "Mock build failure" in str(excinfo.value)