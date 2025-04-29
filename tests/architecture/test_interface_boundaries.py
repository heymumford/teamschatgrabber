"""Tests to verify clean interface boundaries between architectural layers.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import inspect

from teamschatgrab.app import TeamsChatGrabber
from teamschatgrab.api import TeamsApi
from teamschatgrab.storage import TeamsStorage


def test_app_interacts_through_interfaces_only():
    """Test that app layer interacts with outer layers through well-defined interfaces."""
    # Analyze the TeamsChatGrabber constructor and methods
    app_class = TeamsChatGrabber

    # Check constructor
    app_init = app_class.__init__
    app_init_source = inspect.getsource(app_init)

    # App should initialize UI, storage through proper abstraction
    assert "TerminalUI(" in app_init_source
    assert "TeamsStorage(" in app_init_source

    # App methods should use self.ui, self.api, self.storage, not direct imports
    app_methods = [
        method
        for name, method in inspect.getmembers(app_class, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    for method in app_methods:
        source = inspect.getsource(method)

        # For UI operations, app should use self.ui, not direct terminal output
        if "ui" in source:
            assert "self.ui." in source
            assert "print(" not in source

        # For API operations, app should use self.api, not direct API calls
        if "api" in source and "self.api =" not in source:
            assert "self.api." in source
            assert "requests." not in source

        # For storage operations, app should use self.storage, not direct file operations
        if (
            "storage" in source
            and "self.storage =" not in source
            and method.__name__ != "configure_download"
        ):
            assert "self.storage." in source
            assert "open(" not in source
            assert "Path(" not in source


def test_api_provides_clean_interface():
    """Test that API adapter provides clean interface to use cases."""
    api_class = TeamsApi

    # API should provide domain-specific methods, not generic HTTP methods
    api_public_methods = [
        name
        for name, method in inspect.getmembers(api_class, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    # API should have domain-specific methods
    assert "get_chats" in api_public_methods
    assert "get_channels" in api_public_methods
    assert "get_messages" in api_public_methods

    # API should hide HTTP details in private methods
    api_private_methods = [
        name
        for name, method in inspect.getmembers(api_class, predicate=inspect.isfunction)
        if name.startswith("_")
    ]

    # Should have private method for HTTP details
    assert any("request" in name.lower() for name in api_private_methods)

    # Check that public methods use private methods for HTTP details
    for method_name in api_public_methods:
        method = getattr(api_class, method_name)
        source = inspect.getsource(method)

        if "request" in source:
            assert "self._make_request" in source


def test_storage_provides_clean_interface():
    """Test that storage adapter provides clean interface to use cases."""
    storage_class = TeamsStorage

    # Storage should provide domain-specific methods, not generic file methods
    storage_public_methods = [
        name
        for name, method in inspect.getmembers(
            storage_class, predicate=inspect.isfunction
        )
        if not name.startswith("_")
    ]

    # Storage should have domain-specific methods
    assert "create_chat_directory" in storage_public_methods
    assert "save_messages" in storage_public_methods
    assert "save_attachment" in storage_public_methods

    # Storage should hide file system details in private methods
    storage_private_methods = [
        name
        for name, method in inspect.getmembers(
            storage_class, predicate=inspect.isfunction
        )
        if name.startswith("_")
    ]

    # Should have private methods for file system details
    assert any("dir" in name.lower() for name in storage_private_methods)
