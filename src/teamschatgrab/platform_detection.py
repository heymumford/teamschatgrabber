"""
Platform detection and environment-specific utilities.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from enum import Enum
import os
import platform
import sys
from typing import Optional, Dict, Any


class PlatformType(str, Enum):
    """Supported platform types."""

    WINDOWS = "windows"
    MACOS = "macos"
    WSL = "wsl"
    LINUX = "linux"
    UNKNOWN = "unknown"


def detect_platform() -> PlatformType:
    """Detect the current platform."""
    system = platform.system().lower()

    if system == "darwin":
        return PlatformType.MACOS
    elif system == "windows":
        return PlatformType.WINDOWS
    elif system == "linux":
        # Check if running on WSL
        if "microsoft" in platform.uname().release.lower():
            return PlatformType.WSL
        return PlatformType.LINUX

    return PlatformType.UNKNOWN


def get_teams_data_path() -> Optional[str]:
    """Get the platform-specific Teams data path."""
    platform_type = detect_platform()

    if platform_type == PlatformType.WINDOWS:
        # Windows Teams data path
        return os.path.expandvars(r"%APPDATA%\Microsoft\Teams")
    elif platform_type == PlatformType.MACOS:
        # macOS Teams data path
        return os.path.expanduser("~/Library/Application Support/Microsoft/Teams")
    elif platform_type == PlatformType.WSL:
        # WSL (access to Windows AppData)
        username = os.getenv("USER")
        if not username:
            return None
        return f"/mnt/c/Users/{username}/AppData/Roaming/Microsoft/Teams"

    return None


def get_platform_info() -> Dict[str, Any]:
    """Get detailed platform information."""
    return {
        "platform": detect_platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "python_version": sys.version,
        "teams_data_path": get_teams_data_path(),
    }
