"""Tests to verify dependency direction follows clean architecture principles.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import inspect


def test_domain_entities_have_no_external_dependencies():
    """Test that core domain entities don't depend on outer layers."""
    # Core domain entities
    from teamschatgrab.api import ChatType
    from teamschatgrab.storage import StorageFormat

    # Get the ChatType source code
    chat_type_source = inspect.getsource(ChatType)

    # Core entities should not reference adapter modules or external frameworks
    assert "teamschatgrab.ui" not in chat_type_source
    assert "teamschatgrab.app" not in chat_type_source

    # Get the StorageFormat source code
    storage_format_source = inspect.getsource(StorageFormat)

    # Core entities should only depend on standard library
    assert "teamschatgrab.ui" not in storage_format_source
    assert "teamschatgrab.app" not in storage_format_source


def test_use_cases_dont_depend_on_frameworks():
    """Test that use cases don't directly depend on external frameworks."""
    # The main use case orchestrator is in the app module
    from teamschatgrab.app import TeamsChatGrabber

    # Get the source code of the TeamsChatGrabber class
    app_source = inspect.getsource(TeamsChatGrabber)

    # Use cases should not directly import external frameworks
    assert "import requests" not in app_source
    assert "from requests import" not in app_source
    # Rich is a UI framework and should be isolated in UI layer
    assert "import rich" not in app_source
    assert "from rich import" not in app_source


def test_interface_adapters_dont_depend_on_frameworks_directly():
    """Test that interface adapters don't expose framework details to use cases."""
    # The UI adapter should isolate rich library details
    from teamschatgrab.ui import TerminalUI

    # The API adapter should isolate requests library details
    from teamschatgrab.api import TeamsApi

    # Check TerminalUI interface
    terminal_ui_methods = inspect.getmembers(TerminalUI, predicate=inspect.isfunction)
    for name, method in terminal_ui_methods:
        # Public methods should not return framework-specific types
        if not name.startswith("_"):
            signature = inspect.signature(method)
            for param in (
                signature.return_annotation.__args__
                if hasattr(signature.return_annotation, "__args__")
                else [signature.return_annotation]
            ):
                param_str = str(param)
                assert (
                    "rich" not in param_str.lower()
                ), f"UI adapter method {name} returns framework type: {param}"

    # Check TeamsApi interface
    api_methods = inspect.getmembers(TeamsApi, predicate=inspect.isfunction)
    for name, method in api_methods:
        # Public methods should not return framework-specific types
        if not name.startswith("_"):
            signature = inspect.signature(method)
            for param in (
                signature.return_annotation.__args__
                if hasattr(signature.return_annotation, "__args__")
                else [signature.return_annotation]
            ):
                param_str = str(param)
                assert (
                    "requests" not in param_str.lower()
                ), f"API adapter method {name} returns framework type: {param}"
