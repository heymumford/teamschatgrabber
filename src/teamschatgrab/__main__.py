"""
Command-line entry point for Teams chat grabber.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

import argparse
import sys
from typing import Optional, List

from .app import create_app


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Download chat history from Microsoft Teams"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory to save downloaded chats (default: ~/TeamsDownloads)",
        type=str,
    )

    parser.add_argument(
        "--no-rich", help="Disable rich formatting", action="store_true"
    )

    parser.add_argument("--debug", help="Enable debug output", action="store_true")

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point.

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code
    """
    parsed_args = parse_args(args)

    try:
        # Create and run the app
        app = create_app(
            output_dir=parsed_args.output_dir, use_rich_ui=not parsed_args.no_rich
        )

        success = app.run()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        if parsed_args.debug:
            # Re-raise for traceback in debug mode
            raise
        else:
            print(f"Error: {str(e)}")
            print("For more details, run with --debug flag")
            return 1


if __name__ == "__main__":
    sys.exit(main())
