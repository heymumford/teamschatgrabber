"""
User interface for Teams chat grabber.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import os
import platform
import sys
from enum import Enum
from typing import List, Any, Optional

try:
    from rich.console import Console
    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Prompt, Confirm
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class LogLevel(str, Enum):
    """Log levels for the UI."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class TerminalUI:
    """Terminal-based user interface."""

    def __init__(self, use_rich: bool = True):
        """Initialize the terminal UI.

        Args:
            use_rich: Whether to use rich formatting (if available)
        """
        self.use_rich = use_rich and RICH_AVAILABLE

        if self.use_rich:
            self.console = Console()

        # Detect terminal capabilities
        self.is_windows = platform.system().lower() == "windows"
        self.supports_unicode = (
            not self.is_windows or os.environ.get("WT_SESSION") is not None
        )

        # Set appropriate symbols based on terminal capabilities
        if self.supports_unicode:
            self.symbols = {
                LogLevel.DEBUG: "🔍",
                LogLevel.INFO: "ℹ️",
                LogLevel.WARNING: "⚠️",
                LogLevel.ERROR: "❌",
                LogLevel.SUCCESS: "✅",
            }
        else:
            self.symbols = {
                LogLevel.DEBUG: "[D]",
                LogLevel.INFO: "[I]",
                LogLevel.WARNING: "[W]",
                LogLevel.ERROR: "[E]",
                LogLevel.SUCCESS: "[S]",
            }

    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Log a message to the console.

        Args:
            message: Message to log
            level: Log level
        """
        symbol = self.symbols.get(level, "")

        if self.use_rich:
            style_map = {
                LogLevel.DEBUG: "dim",
                LogLevel.INFO: "blue",
                LogLevel.WARNING: "yellow",
                LogLevel.ERROR: "bold red",
                LogLevel.SUCCESS: "green",
            }
            style = style_map.get(level, "")
            self.console.print(f"{symbol} {message}", style=style)
        else:
            # Fallback to plain text
            print(f"{symbol} {message}")

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: Debug message
        """
        self.log(message, LogLevel.DEBUG)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: Info message
        """
        self.log(message, LogLevel.INFO)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: Warning message
        """
        self.log(message, LogLevel.WARNING)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message
        """
        self.log(message, LogLevel.ERROR)

    def success(self, message: str) -> None:
        """Log a success message.

        Args:
            message: Success message
        """
        self.log(message, LogLevel.SUCCESS)

    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Prompt the user for input.

        Args:
            message: Prompt message
            default: Default value

        Returns:
            str: User input
        """
        if self.use_rich:
            return Prompt.ask(message, default=default or "")
        else:
            # Fallback to basic input
            default_str = f" [{default}]" if default else ""
            result = input(f"{message}{default_str}: ")
            return result if result else (default or "")

    def confirm(self, message: str, default: bool = False) -> bool:
        """Prompt the user for confirmation.

        Args:
            message: Confirmation message
            default: Default value

        Returns:
            bool: True if confirmed, False otherwise
        """
        if self.use_rich:
            return Confirm.ask(message, default=default)
        else:
            # Fallback to basic input
            default_str = "[Y/n]" if default else "[y/N]"
            result = input(f"{message} {default_str}: ").lower()

            if not result:
                return default

            return result.startswith("y")

    def select_option(
        self, message: str, options: List[str], descriptions: Optional[List[str]] = None
    ) -> int:
        """Prompt the user to select an option.

        Args:
            message: Prompt message
            options: List of options
            descriptions: Optional descriptions for options

        Returns:
            int: Index of selected option
        """
        self.log(message, LogLevel.INFO)

        if self.use_rich:
            # Display options as a table
            table = Table(title=message)
            table.add_column("#", style="cyan")
            table.add_column("Option", style="green")

            if descriptions:
                table.add_column("Description")

            for i, option in enumerate(options):
                if descriptions and i < len(descriptions):
                    table.add_row(str(i + 1), option, descriptions[i])
                else:
                    table.add_row(str(i + 1), option)

            self.console.print(table)

            # Get selection
            selection = None
            while selection is None:
                try:
                    value = int(Prompt.ask("Enter selection", default="1"))
                    if 1 <= value <= len(options):
                        selection = value - 1
                    else:
                        self.error(
                            f"Please enter a number between 1 and {len(options)}"
                        )
                except ValueError:
                    self.error("Please enter a valid number")

            return selection
        else:
            # Fallback to basic output
            for i, option in enumerate(options):
                if descriptions and i < len(descriptions):
                    print(f"{i+1}. {option} - {descriptions[i]}")
                else:
                    print(f"{i+1}. {option}")

            # Get selection
            selection = None
            while selection is None:
                try:
                    value = int(input("Enter selection: "))
                    if 1 <= value <= len(options):
                        selection = value - 1
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                except ValueError:
                    print("Please enter a valid number")

            return selection

    def progress(self, total: int, description: str = "Progress") -> Any:
        """Create a progress bar.

        Args:
            total: Total number of steps
            description: Progress description

        Returns:
            Any: Progress bar object
        """
        if self.use_rich:
            progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("• [bold]{task.completed}/{task.total}"),
            )
            task = progress.add_task(description, total=total)
            return {"progress": progress, "task": task}
        else:
            # Return a simplified progress tracker
            return {"total": total, "current": 0, "description": description}

    def update_progress(self, progress_obj: Any, advance: int = 1) -> None:
        """Update a progress bar.

        Args:
            progress_obj: Progress bar object
            advance: Amount to advance
        """
        if (
            self.use_rich
            and isinstance(progress_obj, dict)
            and "progress" in progress_obj
        ):
            progress_obj["progress"].update(progress_obj["task"], advance=advance)
        else:
            # Update simplified progress tracker
            progress_obj["current"] += advance
            current = progress_obj["current"]
            total = progress_obj["total"]

            # Display basic progress bar
            width = 40
            filled = int(width * current / total)
            percent = current / total * 100

            bar = (
                f"[{'=' * filled}{' ' * (width - filled)}] {percent:.1f}% "
                f"({current}/{total})"
            )
            sys.stdout.write(f"\r{progress_obj['description']}: {bar}")
            sys.stdout.flush()

            if current >= total:
                print()  # Add a newline at the end

    def start_progress(self, progress_obj: Any) -> None:
        """Start a progress bar context.

        Args:
            progress_obj: Progress bar object
        """
        if (
            self.use_rich
            and isinstance(progress_obj, dict)
            and "progress" in progress_obj
        ):
            progress_obj["progress"].start()

    def stop_progress(self, progress_obj: Any) -> None:
        """Stop a progress bar context.

        Args:
            progress_obj: Progress bar object
        """
        if (
            self.use_rich
            and isinstance(progress_obj, dict)
            and "progress" in progress_obj
        ):
            progress_obj["progress"].stop()

    def display_table(
        self, headers: List[str], rows: List[List[str]], title: Optional[str] = None
    ) -> None:
        """Display data as a table.

        Args:
            headers: Table headers
            rows: Table rows
            title: Optional table title
        """
        if self.use_rich:
            table = Table(title=title)

            for header in headers:
                table.add_column(header)

            for row in rows:
                table.add_row(*row)

            self.console.print(table)
        else:
            # Fallback to basic table display
            if title:
                print(f"\n{title}")

            # Calculate column widths
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell))

            # Print headers
            header_row = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
            print(header_row)
            print("-" * len(header_row))

            # Print rows
            for row in rows:
                print(" | ".join(f"{cell:<{w}}" for cell, w in zip(row, col_widths)))
