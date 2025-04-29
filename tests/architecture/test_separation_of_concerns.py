"""Tests to verify proper separation of concerns across architectural layers.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import inspect

from teamschatgrab.app import TeamsChatGrabber
from teamschatgrab.api import TeamsApi
from teamschatgrab.ui import TerminalUI
from teamschatgrab.storage import TeamsStorage
from teamschatgrab.platform_detection import get_teams_data_path


def test_ui_logic_separated_from_business_logic():
    """Test that UI logic is separated from business logic."""
    # Analyze app and UI classes
    app_methods = inspect.getmembers(TeamsChatGrabber, predicate=inspect.isfunction)
    ui_methods = inspect.getmembers(TerminalUI, predicate=inspect.isfunction)

    app_method_names = [name for name, _ in app_methods]
    ui_method_names = [name for name, _ in ui_methods]

    # UI methods should be in UI class, not in app class
    ui_specific_methods = [
        "log",
        "info",
        "error",
        "warning",
        "success",
        "prompt",
        "select_option",
        "confirm",
        "progress",
        "display_table",
    ]

    for method in ui_specific_methods:
        assert method in ui_method_names, f"UI method {method} not found in UI class"
        assert method not in app_method_names, f"UI method {method} found in app class"

    # Business logic methods should be in app class, not in UI class
    business_methods = [
        "check_environment",
        "authenticate",
        "list_chats",
        "select_chat",
        "configure_download",
        "download_chat",
    ]

    for method in business_methods:
        assert (
            method in app_method_names
        ), f"Business method {method} not found in app class"
        assert (
            method not in ui_method_names
        ), f"Business method {method} found in UI class"

    # App methods should not contain UI rendering code
    for name, method in app_methods:
        if name in business_methods:
            source = inspect.getsource(method)
            assert (
                "print(" not in source
            ), f"Direct print statement found in business method {name}"
            assert (
                "input(" not in source
            ), f"Direct input statement found in business method {name}"


def test_platform_detection_responsibilities():
    """Test that platform detection has proper responsibility allocation."""
    # Platform detection should be responsible for determining platform-specific paths
    # Other modules should delegate this responsibility to platform_detection

    # TerminalUI has a legitimate need to detect platform for terminal capabilities
    # but should not have platform-specific path logic

    # Check that app class uses platform_detection module
    app_source = inspect.getsource(TeamsChatGrabber)
    assert "platform_info = get_platform_info()" in app_source

    # The app should not implement its own platform detection
    assert "platform.system()" not in app_source
    assert "os.name" not in app_source

    # Platform-specific paths should be determined in platform_detection module
    platform_detection_source = inspect.getsource(get_teams_data_path)

    # Platform detection module should handle different paths per platform
    assert (
        "Windows" in platform_detection_source or "windows" in platform_detection_source
    )
    assert "MACOS" in platform_detection_source or "Darwin" in platform_detection_source

    # The module should return platform-specific paths
    assert (
        "return os.path.expandvars" in platform_detection_source
        or "return os.path.expanduser" in platform_detection_source
    )


def test_data_persistence_responsibilities():
    """Test that data persistence has proper responsibility allocation."""
    # Check that app class delegates file operations to storage module
    app_download_chat = inspect.getsource(TeamsChatGrabber.download_chat)

    # App should use storage for file operations
    assert "self.storage.create_chat_directory" in app_download_chat
    assert "self.storage.save_messages" in app_download_chat

    # App should not perform direct file operations
    assert "open(" not in app_download_chat
    assert "with open" not in app_download_chat

    # Storage module should be responsible for file operations
    storage_save_messages = inspect.getsource(TeamsStorage.save_messages)

    # Storage should handle different file formats
    assert "open(" in storage_save_messages or "with open" in storage_save_messages
    assert "json.dump" in storage_save_messages or "write(" in storage_save_messages

    # Check that API doesn't do file operations
    api_source = inspect.getsource(TeamsApi)
    assert "open(" not in api_source
    assert "Path(" not in api_source


def test_error_handling_pattern():
    """Test that error handling follows clean architecture principles."""
    # Verify each layer defines its own exceptions
    from teamschatgrab.api import TeamsApiError
    from teamschatgrab.auth import TeamsAuthError
    from teamschatgrab.storage import StorageError

    # Each layer should have domain-specific exceptions for better error handling
    assert issubclass(TeamsApiError, Exception)
    assert issubclass(TeamsAuthError, Exception)
    assert issubclass(StorageError, Exception)

    # App should catch and handle errors from lower layers in its public interface
    download_chat_method = TeamsChatGrabber.download_chat
    download_chat_source = inspect.getsource(download_chat_method)

    # App should protect its public interface with error handling
    assert "try:" in download_chat_source
    assert "except" in download_chat_source

    # API should handle network errors and translate them to domain exceptions
    api_request_method = TeamsApi._make_request
    api_request_source = inspect.getsource(api_request_method)

    # API should catch external exceptions and throw domain-specific ones
    assert "except requests.RequestException" in api_request_source
    assert "raise TeamsApiError" in api_request_source

    # Storage should handle file system errors
    storage_save = TeamsStorage.save_messages
    storage_save_source = inspect.getsource(storage_save)

    # Storage should protect against file system errors
    assert "try:" in storage_save_source
    assert "except" in storage_save_source
    assert "raise StorageError" in storage_save_source
