"""
Main application logic for Teams chat grabber.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, TypedDict

from .api import TeamsApi, TeamsApiError, ChatType
from .auth import TeamsAuthError, get_current_user_info, validate_token
from .platform_detection import get_platform_info, PlatformType
from .storage import TeamsStorage, StorageFormat, StorageError
from .ui import TerminalUI


class DownloadConfig(TypedDict, total=False):
    """Configuration for download options."""

    format: StorageFormat
    limit: Optional[int]
    date_from: Optional[datetime.datetime]
    date_to: Optional[datetime.datetime]


class TeamsChatGrabber:
    """Main application for downloading Teams chat history."""

    def __init__(self, output_dir: Optional[str] = None, use_rich_ui: bool = True):
        """Initialize the Teams chat grabber.

        Args:
            output_dir: Custom output directory
            use_rich_ui: Whether to use rich formatting
        """
        self.ui: TerminalUI = TerminalUI(use_rich=use_rich_ui)
        self.platform_info = get_platform_info()
        self.storage: TeamsStorage = TeamsStorage(base_path=output_dir)
        self.api: Optional[TeamsApi] = None
        self.user_info: Optional[Dict[str, Any]] = None

    def check_environment(self) -> bool:
        """Check if the environment is suitable for running.

        Returns:
            bool: True if environment check passed
        """
        platform_type = self.platform_info["platform"]

        self.ui.info(f"Platform detected: {platform_type.value}")

        if platform_type == PlatformType.UNKNOWN:
            self.ui.error("Unsupported platform")
            return False

        if not self.platform_info["teams_data_path"]:
            self.ui.error("Microsoft Teams data path not found")
            return False

        if not os.path.exists(self.platform_info["teams_data_path"]):
            self.ui.error(
                f"Teams data path not found: "
                f"{self.platform_info['teams_data_path']}"
            )
            return False

        self.ui.success("Environment check passed")
        return True

    def authenticate(self) -> bool:
        """Authenticate with Teams.

        Returns:
            bool: True if authentication succeeded
        """
        self.ui.info("Checking for logged-in Teams user...")

        try:
            self.user_info = get_current_user_info()

            if not self.user_info:
                self.ui.error("No logged-in Teams user found")
                self.ui.info("Please log in to Microsoft Teams application first")
                return False

            self.ui.success(
                f"Found logged-in user: {self.user_info['name']} "
                f"({self.user_info['email']})"
            )

            # Validate the token
            is_valid, error = validate_token(self.user_info["token"])
            if not is_valid:
                self.ui.error(f"Invalid authentication token: {error}")
                self.ui.info("Please log in to Microsoft Teams application again")
                return False

            # Create API client
            self.api = TeamsApi(token=self.user_info["token"])

            return True

        except TeamsAuthError as e:
            self.ui.error(f"Authentication error: {str(e)}")
            return False

    def list_chats(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """List available chats and channels.

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
                Tuple of (chats, channels)
        """
        if not self.api:
            self.ui.error("Not authenticated")
            return [], []

        self.ui.info("Fetching available chats...")

        try:
            # Get direct and group chats
            chats_data = self.api.get_chats()

            # Extract list of chats from response
            chats: List[Dict[str, Any]] = []
            if isinstance(chats_data, dict):
                for key, value in chats_data.items():
                    if isinstance(value, list):
                        chats = value
                        break
                if not chats and chats_data:
                    # Single chat as dict
                    chats = [chats_data]
            elif isinstance(chats_data, list):
                chats = chats_data

            # Get teams and their channels
            channels: List[Dict[str, Any]] = []
            # This would need to be implemented to get teams and then channels
            # for each team

            self.ui.success(f"Found {len(chats)} chats and {len(channels)} channels")
            return chats, channels

        except TeamsApiError as e:
            self.ui.error(f"Failed to fetch chats: {str(e)}")
            return [], []

    def select_chat(
        self, chats: List[Dict[str, Any]], channels: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], ChatType]:
        """Prompt user to select a chat to download.

        Args:
            chats: List of available chats
            channels: List of available channels

        Returns:
            Tuple[Optional[Dict[str, Any]], ChatType]:
                Selected chat/channel and its type
        """
        if not chats and not channels:
            self.ui.error("No chats or channels available")
            return None, ChatType.DIRECT

        # Combine options for selection
        options = []
        descriptions = []

        for chat in chats:
            chat_type = "Group" if chat.get("isGroup", False) else "Direct"
            participants = ", ".join(
                [p.get("displayName", "Unknown") for p in chat.get("participants", [])]
            )

            options.append(f"{chat.get('displayName', 'Unnamed Chat')}")
            descriptions.append(f"{chat_type} chat with {participants}")

        for channel in channels:
            team_name = channel.get("team", {}).get("displayName", "Unknown Team")
            options.append(
                f"{channel.get('displayName', 'Unnamed Channel')} " f"({team_name})"
            )
            descriptions.append("Team channel")

        # Let user select
        selection = self.ui.select_option(
            "Select a chat to download:", options, descriptions
        )

        # Determine what was selected
        if selection < len(chats):
            return (
                chats[selection],
                (
                    ChatType.DIRECT
                    if not chats[selection].get("isGroup", False)
                    else ChatType.GROUP
                ),
            )
        else:
            channel_idx = selection - len(chats)
            return channels[channel_idx], ChatType.CHANNEL

    def configure_download(self) -> DownloadConfig:
        """Configure download options.

        Returns:
            DownloadConfig: Download configuration
        """
        config: DownloadConfig = {}

        # Output format
        format_options = [f.value for f in StorageFormat]
        format_idx = self.ui.select_option("Select output format:", format_options)
        selected_format = format_options[format_idx]
        selected_storage_format = StorageFormat(selected_format)
        config["format"] = selected_storage_format  # This is a StorageFormat enum

        # Message limit
        limit_str = self.ui.prompt(
            "Maximum messages to download (leave empty for all):", ""
        )
        limit_value: Optional[int] = None
        if limit_str and limit_str.isdigit():
            limit_value = int(limit_str)
        config["limit"] = limit_value  # This is an Optional[int]

        # Date range
        use_date_range = self.ui.confirm("Filter by date range?", False)

        if use_date_range:
            date_from_str = self.ui.prompt(
                "From date (YYYY-MM-DD, leave empty for no limit):", ""
            )
            date_to_str = self.ui.prompt(
                "To date (YYYY-MM-DD, leave empty for today):", ""
            )

            try:
                # Handle date parsing
                # Initialize date variables
                date_from_value: Optional[datetime.datetime] = None
                if date_from_str:
                    # Parse date from input string
                    date_from_value = datetime.datetime.strptime(
                        date_from_str, "%Y-%m-%d"
                    )
                config["date_from"] = date_from_value  # This is an Optional[datetime]

                date_to_value: datetime.datetime = datetime.datetime.now()
                if date_to_str:
                    date_to_value = datetime.datetime.strptime(date_to_str, "%Y-%m-%d")
                config["date_to"] = date_to_value  # This is a datetime
            except ValueError:
                self.ui.warning("Invalid date format, ignoring date range")
                # Handle the error case properly
                date_from_none: Optional[datetime.datetime] = None
                date_to_none: Optional[datetime.datetime] = None
                config["date_from"] = date_from_none
                config["date_to"] = date_to_none

        return config

    def download_chat(
        self, chat: Dict[str, Any], chat_type: ChatType, config: DownloadConfig
    ) -> Optional[Path]:
        """Download chat history.

        Args:
            chat: Chat or channel to download
            chat_type: Type of chat
            config: Download configuration

        Returns:
            Optional[Path]: Path to downloaded chat
        """
        if not self.api:
            self.ui.error("Not authenticated")
            return None

        chat_id = chat.get("id", "")
        if not chat_id:  # Ensure chat_id is not None or empty
            self.ui.error("Invalid chat: missing ID")
            return None
        chat_name = chat.get("displayName", "Unnamed Chat")

        self.ui.info(f"Downloading {chat_type.value} chat: {chat_name}")

        try:
            # Create chat directory
            chat_dir = self.storage.create_chat_directory(
                chat_name=chat_name, chat_id=chat_id, chat_type=chat_type
            )

            # Get messages
            self.ui.info("Fetching messages...")

            messages = []
            total_fetched = 0
            limit = config.get("limit")
            date_from = config.get("date_from")
            date_to = config.get("date_to")

            # Create progress bar
            progress = self.ui.progress(
                total=limit or 1000,  # If no limit, start with estimated 1000
                description="Fetching messages",
            )
            self.ui.start_progress(progress)

            try:
                for message in self.api.get_all_messages(
                    chat_id=chat_id, chat_type=chat_type, limit=limit
                ):
                    # Apply date filtering if configured
                    if date_from or date_to:
                        msg_date = datetime.datetime.fromisoformat(
                            message.get("createdDateTime", "")
                        )

                        if date_from and msg_date < date_from:
                            continue

                        if date_to and msg_date > date_to:
                            continue

                    messages.append(message)
                    total_fetched += 1

                    self.ui.update_progress(progress)

                    # Check if we reached the limit
                    if limit and total_fetched >= limit:
                        break
            finally:
                self.ui.stop_progress(progress)

            if not messages:
                self.ui.warning("No messages found")
                return chat_dir

            self.ui.success(f"Downloaded {len(messages)} messages")

            # Save messages
            format_value = config.get("format", StorageFormat.JSON)

            self.ui.info(f"Saving messages in {format_value.value} format...")
            saved_path = self.storage.save_messages(
                messages=messages, chat_dir=chat_dir, format=format_value
            )

            self.ui.success(f"Saved messages to: {saved_path}")

            # TODO: Handle attachments

            return chat_dir

        except (TeamsApiError, StorageError) as e:
            self.ui.error(f"Download failed: {str(e)}")
            return None

    def run(self) -> bool:
        """Run the complete chat grabber flow.

        Returns:
            bool: True if successful
        """
        self.ui.info("Teams Chat Grabber")

        # Check environment
        if not self.check_environment():
            return False

        # Authenticate
        if not self.authenticate():
            return False

        # List chats
        chats, channels = self.list_chats()
        if not chats and not channels:
            return False

        # Select chat
        selected_chat, chat_type = self.select_chat(chats, channels)
        if not selected_chat:
            return False

        # Configure download
        config = self.configure_download()

        # Download chat
        chat_dir = self.download_chat(selected_chat, chat_type, config)
        if not chat_dir:
            return False

        self.ui.success(f"Chat downloaded to: {chat_dir}")
        return True


def create_app(
    output_dir: Optional[str] = None, use_rich_ui: bool = True
) -> TeamsChatGrabber:
    """Create a Teams chat grabber application.

    Args:
        output_dir: Custom output directory
        use_rich_ui: Whether to use rich formatting

    Returns:
        TeamsChatGrabber: Application instance
    """
    return TeamsChatGrabber(output_dir=output_dir, use_rich_ui=use_rich_ui)
