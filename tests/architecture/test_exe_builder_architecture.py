"""Tests for exe_builder module architecture.

Verifies that the exe_builder module follows the project's architectural principles.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import inspect
from pathlib import Path

import pytest

from teamschatgrab.exe_builder import ExeBuilder, build_exe


class TestExeBuilderArchitecture:
    """Tests for exe_builder module architecture."""

    def test_separation_of_concerns(self):
        """Verify the module has proper separation of concerns."""
        # The ExeBuilder class should be responsible for building executables
        # The build_exe function should be responsible for platform detection
        
        # Check that the class and function are properly focused
        assert "build_windows_exe" in dir(ExeBuilder)
        assert "build_exe" in globals()
        
        # ExeBuilder method should not contain platform detection logic
        exe_builder_source = inspect.getsource(ExeBuilder.build_windows_exe)
        assert "sys.platform" not in exe_builder_source
        
        # build_exe function should contain platform detection
        build_exe_source = inspect.getsource(build_exe)
        assert "sys.platform" in build_exe_source

    def test_dependency_direction(self):
        """Test that dependencies flow in the correct direction."""
        # ExeBuilder should not depend on the main application
        # It should be a standalone utility that the application depends on
        exe_builder_source = inspect.getsource(ExeBuilder)
        
        # Should not import from other teamschatgrab modules
        assert "from teamschatgrab.app import" not in exe_builder_source
        assert "from teamschatgrab.api import" not in exe_builder_source
        assert "from teamschatgrab.auth import" not in exe_builder_source
        assert "from teamschatgrab.ui import" not in exe_builder_source
        
        # Should have minimal dependencies
        assert exe_builder_source.count("import ") < 5

    def test_interface_boundaries(self):
        """Test that the module has clear interface boundaries."""
        # Check public interface is well-defined
        assert hasattr(ExeBuilder, "__init__")
        assert hasattr(ExeBuilder, "build_windows_exe")
        
        # The public function should have clear parameters
        signature = inspect.signature(build_exe)
        assert "name" in signature.parameters
        assert "onefile" in signature.parameters
        assert "console" in signature.parameters
        
        # All public methods should have docstrings
        assert ExeBuilder.__init__.__doc__ is not None
        assert ExeBuilder.build_windows_exe.__doc__ is not None
        assert build_exe.__doc__ is not None

    def test_substitutability(self):
        """Test that the module supports substitutability."""
        # You should be able to create an ExeBuilder with a custom base path
        custom_path = Path("/custom/path")
        builder = ExeBuilder(base_path=custom_path)
        
        # The builder should use the provided path
        assert builder.base_path == custom_path
        assert builder.dist_path == custom_path / "dist"
        
        # Methods should support parameter customization
        method = ExeBuilder.build_windows_exe
        signature = inspect.signature(method)
        
        # Default parameters should exist but be overridable
        assert signature.parameters["name"].default == "TeamsChatGrabber"
        assert signature.parameters["onefile"].default is True
        assert signature.parameters["console"].default is False
        
        # Return value should be well-defined and documented
        assert "Returns:" in method.__doc__
        assert "Path" in method.__doc__