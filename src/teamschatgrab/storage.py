"""
Storage module for saving Teams messages and attachments.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import datetime
import json
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from .api import ChatType


class StorageFormat(str, Enum):
    """Supported output formats for saving messages."""

    JSON = "json"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"


class StorageError(Exception):
    """Exception raised for storage-related errors."""

    pass


class TeamsStorage:
    """Storage handler for Teams messages and attachments."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize storage handler.

        Args:
            base_path: Base directory for storing downloaded content
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to user's home directory
            self.base_path = Path.home() / "TeamsDownloads"

        # Ensure base directory exists
        self._ensure_dir(self.base_path)

    def _ensure_dir(self, path: Path) -> None:
        """Ensure directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure

        Raises:
            StorageError: If directory creation fails
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create directory {path}: {e}") from e

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename.

        Args:
            name: Original string

        Returns:
            str: Sanitized filename
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."
        return sanitized

    def create_chat_directory(
        self, chat_name: str, chat_id: str, chat_type: ChatType
    ) -> Path:
        """Create a directory for storing chat messages and attachments.

        Args:
            chat_name: Human-readable chat name
            chat_id: Chat or channel ID
            chat_type: Type of chat

        Returns:
            Path: Path to the created directory
        """
        sanitized_name = self._sanitize_filename(chat_name)
        # Create a directory with both name and ID to ensure uniqueness
        dir_name = f"{sanitized_name}_{chat_id[-8:]}"

        # Organize by chat type
        type_dir = self.base_path / chat_type.value
        chat_dir = type_dir / dir_name

        self._ensure_dir(chat_dir)
        self._ensure_dir(chat_dir / "attachments")

        return chat_dir

    def save_messages(
        self,
        messages: List[Dict[str, Any]],
        chat_dir: Path,
        format: StorageFormat = StorageFormat.JSON,
    ) -> Path:
        """Save messages to a file.

        Args:
            messages: List of message objects
            chat_dir: Directory to save messages in
            format: Output format

        Returns:
            Path: Path to the saved file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == StorageFormat.JSON:
            file_path = chat_dir / f"messages_{timestamp}.json"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(messages, f, indent=2, ensure_ascii=False)
            except Exception as e:
                raise StorageError(
                    f"Failed to save messages to {file_path}: {e}"
                ) from e

        elif format == StorageFormat.TEXT:
            file_path = chat_dir / f"messages_{timestamp}.txt"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for msg in messages:
                        sender = (
                            msg.get("sender", {})
                            .get("user", {})
                            .get("displayName", "Unknown")
                        )
                        timestamp = msg.get("createdDateTime", "")
                        content = msg.get("body", {}).get("content", "")

                        f.write(f"From: {sender}\n")
                        f.write(f"Time: {timestamp}\n")
                        f.write(f"Message: {content}\n")
                        f.write("-" * 50 + "\n\n")
            except Exception as e:
                raise StorageError(
                    f"Failed to save messages to {file_path}: {e}"
                ) from e

        elif format == StorageFormat.HTML:
            file_path = chat_dir / f"messages_{timestamp}.html"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("<html><head><title>Teams Chat</title></head><body>\n")
                    f.write("<div class='messages'>\n")

                    for msg in messages:
                        sender = (
                            msg.get("sender", {})
                            .get("user", {})
                            .get("displayName", "Unknown")
                        )
                        timestamp = msg.get("createdDateTime", "")
                        content = msg.get("body", {}).get("content", "")

                        f.write("<div class='message'>\n")
                        f.write(f"  <div class='sender'>{sender}</div>\n")
                        f.write(f"  <div class='time'>{timestamp}</div>\n")
                        f.write(f"  <div class='content'>{content}</div>\n")
                        f.write("</div>\n")

                    f.write("</div></body></html>\n")
            except Exception as e:
                raise StorageError(
                    f"Failed to save messages to {file_path}: {e}"
                ) from e

        elif format == StorageFormat.MARKDOWN:
            file_path = chat_dir / f"messages_{timestamp}.md"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("# Teams Chat Export\n\n")

                    for msg in messages:
                        sender = (
                            msg.get("sender", {})
                            .get("user", {})
                            .get("displayName", "Unknown")
                        )
                        timestamp = msg.get("createdDateTime", "")
                        content = msg.get("body", {}).get("content", "")

                        f.write(f"## {sender} - {timestamp}\n\n")
                        f.write(f"{content}\n\n")
                        f.write("---\n\n")
            except Exception as e:
                raise StorageError(
                    f"Failed to save messages to {file_path}: {e}"
                ) from e

        else:
            raise StorageError(f"Unsupported output format: {format}")

        return file_path

    def save_attachment(
        self, attachment_data: bytes, filename: str, chat_dir: Path
    ) -> Path:
        """Save an attachment to the chat directory.

        Args:
            attachment_data: Binary attachment data
            filename: Original filename
            chat_dir: Chat directory

        Returns:
            Path: Path to the saved attachment
        """
        sanitized_name = self._sanitize_filename(filename)
        file_path = chat_dir / "attachments" / sanitized_name

        try:
            with open(file_path, "wb") as f:
                f.write(attachment_data)
        except Exception as e:
            raise StorageError(f"Failed to save attachment {filename}: {e}") from e

        return file_path
