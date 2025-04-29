"""
Teams API client for fetching conversations and messages.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import datetime
import time
from enum import Enum
from typing import Dict, Optional, Any, Iterator

import requests

from .auth import TeamsAuthError


class ChatType(str, Enum):
    """Types of chats available in Teams."""

    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"


class TeamsApiError(Exception):
    """Exception raised for Teams API errors."""

    pass


class TeamsApi:
    """Client for interacting with Microsoft Teams API."""

    BASE_URL = "https://teams.microsoft.com/api/csa/api"

    def __init__(self, token: str):
        """Initialize the Teams API client.

        Args:
            token: Authentication token for Teams API
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Teams Client)",
            }
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Teams API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: URL parameters
            data: Request body data

        Returns:
            Dict[str, Any]: Response data

        Raises:
            TeamsApiError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = None

        try:
            response = self.session.request(
                method=method, url=url, params=params, json=data
            )

            response.raise_for_status()
            json_data = response.json()
            return dict(json_data) if json_data else {}

        except requests.RequestException as e:
            if response and response.status_code == 401:
                raise TeamsAuthError("Authentication token expired or invalid") from e
            raise TeamsApiError(f"API request failed: {str(e)}") from e

    def get_chats(self) -> Dict[str, Any]:
        """Get list of available chats.

        Returns:
            Dict[str, Any]: Chat data response
        """
        # This is a placeholder - actual endpoint would be determined
        # by reverse engineering the Teams client
        return self._make_request("GET", "chats")

    def get_channels(self, team_id: str) -> Dict[str, Any]:
        """Get list of channels in a team.

        Args:
            team_id: Team ID

        Returns:
            Dict[str, Any]: Channel data response
        """
        # This is a placeholder - actual endpoint would be determined
        # by reverse engineering the Teams client
        return self._make_request("GET", f"teams/{team_id}/channels")

    def get_messages(
        self,
        chat_id: str,
        chat_type: ChatType,
        limit: Optional[int] = None,
        before_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        """Get messages from a chat.

        Args:
            chat_id: Chat or channel ID
            chat_type: Type of chat (direct, group, or channel)
            limit: Maximum number of messages to fetch
            before_date: Only fetch messages before this date

        Returns:
            Dict[str, Any]: Message data response
        """
        # This is a placeholder - actual endpoint would be determined
        # by reverse engineering the Teams client

        endpoint = "messages"
        if chat_type == ChatType.CHANNEL:
            endpoint = f"channels/{chat_id}/messages"
        else:
            endpoint = f"chats/{chat_id}/messages"

        params = {}
        if limit:
            # Ensure limit is properly typed for the API
            params["limit"] = str(limit)
        if before_date:
            # Convert to string to avoid type error
            params["before"] = before_date.isoformat()

        return self._make_request("GET", endpoint, params=params)

    def get_all_messages(
        self, chat_id: str, chat_type: ChatType, limit: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """Get all messages from a chat with pagination.

        Args:
            chat_id: Chat or channel ID
            chat_type: Type of chat
            limit: Total maximum number of messages to fetch

        Yields:
            Dict[str, Any]: Individual message objects
        """
        # Placeholder for pagination logic
        messages_fetched = 0
        last_date = None

        while True:
            response = self.get_messages(
                chat_id=chat_id,
                chat_type=chat_type,
                limit=100,  # Fetch in batches of 100
                before_date=last_date,
            )

            # Extract messages from the response
            messages = []
            if isinstance(response, dict):
                # Try to find messages in response
                for key, value in response.items():
                    if isinstance(value, list):
                        messages = value
                        break
                # If no list found, check if the response itself is a message
                if not messages and "id" in response:
                    messages = [response]
            elif isinstance(response, list):
                messages = response

            if not messages:
                break

            for message in messages:
                yield message
                messages_fetched += 1

                if limit and messages_fetched >= limit:
                    return

            # Update pagination cursor
            if messages and len(messages) > 0:
                last_message = messages[-1]
                created_date = last_message.get("createdDateTime", "")
                if created_date:
                    last_date = datetime.datetime.fromisoformat(created_date)

            # Avoid rate limiting
            time.sleep(0.5)
