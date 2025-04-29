"""
Module for building executable versions of the application.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from typing import Optional
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ExeBuilder:
    """Handles building standalone executable versions of the application."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the executable builder.

        Args:
            base_path: Base path for the application
        """
        self.base_path = base_path or Path(
            os.path.abspath(os.path.dirname(sys.argv[0]))
        )
        self.dist_path = self.base_path / "dist"

    def build_windows_exe(
        self,
        name: str = "TeamsChatGrabber",
        onefile: bool = True,
        console: bool = False,
    ) -> Path:
        """Build a Windows executable.

        Args:
            name: Name of the executable
            onefile: Whether to package as a single file
            console: Whether to show a console window

        Returns:
            Path to the created executable

        Raises:
            ImportError: If PyInstaller is not installed
            RuntimeError: If the build fails
        """
        try:
            import PyInstaller.__main__  # type: ignore
        except ImportError:
            raise ImportError(
                "PyInstaller is required to build executables. "
                "Install it with 'pip install pyinstaller'"
            )

        main_script = self.base_path / "main.py"
        if not main_script.exists():
            raise FileNotFoundError(f"Entry point not found: {main_script}")

        logger.info(f"Building Windows executable: {name}")

        args = [
            str(main_script),
            f"--name={name}",
        ]

        if onefile:
            args.append("--onefile")

        if not console:
            args.append("--noconsole")

        # Add LICENSE to the bundle
        license_path = self.base_path / "LICENSE"
        if license_path.exists():
            args.append(f"--add-data={license_path}:.")

        # Add any other necessary files or data here

        try:
            logger.debug(f"Running PyInstaller with args: {args}")
            PyInstaller.__main__.run(args)

            exe_path = self.dist_path / f"{name}.exe"
            if not exe_path.exists():
                error_msg = f"Expected executable not found: {exe_path}"
                raise RuntimeError(error_msg)

            logger.info(f"Successfully built executable: {exe_path}")
            return exe_path

        except Exception as e:
            logger.error(f"Failed to build executable: {e}")
            raise RuntimeError(f"Failed to build executable: {e}")


def build_exe(
    name: str = "TeamsChatGrabber", onefile: bool = True, console: bool = False
) -> Path:
    """Build a platform-specific executable.

    Args:
        name: Name of the executable
        onefile: Whether to package as a single file
        console: Whether to show a console window

    Returns:
        Path to the created executable

    Raises:
        ImportError: If PyInstaller is not installed
        RuntimeError: If the build fails
        NotImplementedError: If platform is not supported
    """
    builder = ExeBuilder()

    if sys.platform.startswith("win"):
        return builder.build_windows_exe(name, onefile, console)
    else:
        raise NotImplementedError(
            f"Building executables on {sys.platform} is not yet supported"
        )
