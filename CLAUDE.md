# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands
- Run script: `python main.py` or `poetry run teamschatgrab`
- Install dependencies: `pip install -r requirements.txt` or `poetry install`
- Run formatting: `black src tests`
- Run linting: `flake8 src tests`
- Run type checking: `mypy src`
- Run tests (all): `pytest` or `pytest --cov=teamschatgrab`
- Run tests (single): `pytest tests/unit/test_file.py::test_function`
- Build package: `poetry build`

## Code Style Guidelines
- **Python Version**: Support Python 3.8+ for cross-platform compatibility
- **Formatting**: Follow PEP 8 standards with Black (88 character line length)
- **Imports**: Group imports (standard library, third-party, local) with blank lines between
- **Types**: Use type hints throughout with MyPy validation (disallow_untyped_defs=true)
- **Error Handling**: Use specific exceptions with clear error messages for user feedback
- **Cross-platform**: Test paths and commands for both Mac and Windows WSL environments
- **Logging**: Use Python's logging module for tracking progress and errors
- **CLI Interface**: Use Typer (based on argparse) for command-line options
- **File Structure**: Modular design with separate modules for Teams API, auth, and file handling
- **Package Management**: Poetry preferred for dependency management