"""Tests for main module.

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License
"""

from unittest import mock

import pytest

from teamschatgrab.__main__ import main, parse_args


@pytest.fixture
def mock_app():
    """Mock app creation and running."""
    with mock.patch("teamschatgrab.__main__.create_app") as mock_create_app:
        app_instance = mock_create_app.return_value
        app_instance.run.return_value = True
        yield {"create": mock_create_app, "instance": app_instance}


class TestMain:
    """Tests for main module."""

    def test_parse_args_defaults(self):
        """Test parsing command-line arguments with defaults."""
        args = parse_args([])

        assert args.output_dir is None
        assert args.no_rich is False
        assert args.debug is False

    def test_parse_args_custom(self):
        """Test parsing command-line arguments with custom values."""
        args = parse_args(["-o", "/custom/path", "--no-rich", "--debug"])

        assert args.output_dir == "/custom/path"
        assert args.no_rich is True
        assert args.debug is True

    def test_main_success(self, mock_app):
        """Test successful main execution."""
        result = main(["-o", "/custom/path"])

        assert result == 0
        assert mock_app["create"].called
        mock_app["create"].assert_called_with(
            output_dir="/custom/path", use_rich_ui=True
        )
        assert mock_app["instance"].run.called

    def test_main_failure(self, mock_app):
        """Test failed main execution."""
        mock_app["instance"].run.return_value = False

        result = main([])

        assert result == 1
        assert mock_app["create"].called
        assert mock_app["instance"].run.called

    def test_main_keyboard_interrupt(self, mock_app, capsys):
        """Test keyboard interrupt during execution."""
        mock_app["instance"].run.side_effect = KeyboardInterrupt()

        result = main([])

        assert result == 130
        captured = capsys.readouterr()
        assert "cancelled by user" in captured.out

    def test_main_exception(self, mock_app, capsys):
        """Test exception during execution."""
        mock_app["instance"].run.side_effect = ValueError("Test error")

        result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Test error" in captured.out
        assert "run with --debug flag" in captured.out

    def test_main_exception_debug(self, mock_app):
        """Test exception during execution in debug mode."""
        mock_app["instance"].run.side_effect = ValueError("Test error")

        with pytest.raises(ValueError):
            main(["--debug"])
