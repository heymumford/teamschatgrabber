# Teams Chat Grabber

A cross-platform tool for downloading and archiving Microsoft Teams chat history, detecting your currently logged-in Teams user and saving conversations from direct chats, group chats, and team channels.

## Features

### Core Functionality
- Downloads conversations from direct chats, group chats, and team channels
- Detects and uses your current Teams logged-in user (no separate authentication)
- Saves messages in multiple formats (JSON, text, HTML, Markdown)
- Filters by date range and/or message count

### Technical Features
- Cross-platform support (macOS, Windows, and WSL)
- Clean architecture with separation of concerns
- Rich terminal UI with progress reporting
- Robust error handling and debugging options

## Installation

### Prerequisites
- Python 3.8 or higher
- Microsoft Teams desktop application installed and logged in
- Poetry (recommended) or pip for dependency management

### Option 1: Build Script (Recommended)

**On macOS/Linux:**
```bash
# Make the script executable if needed
chmod +x build.sh

# Run the build script
./build.sh
```

**On Windows:**
```bash
build.bat
```

This will:
- Install all dependencies
- Format the code with Black
- Run linting and type checking
- Run tests
- Build the package
- Show usage instructions

### Option 2: Manual Installation

```bash
# With Poetry
poetry install
poetry shell

# With pip
pip install -r requirements.txt
```

## Usage

### Quick Start

#### Option 1: One-Command Launch (Recommended)

```bash
# On macOS/Linux:
./build.sh run

# On Windows:
build.bat run
```

#### Option 2: Manual Activation

```bash
# On macOS/Linux:
source $(poetry env info --path)/bin/activate
teamschatgrab

# On Windows (in Command Prompt):
for /f "tokens=*" %i in ('poetry env info --path') do set VENV_PATH=%i
call %VENV_PATH%\Scripts\activate.bat
teamschatgrab

# If using pip
python main.py
```

### Command-Line Options

```
usage: teamschatgrab [-h] [-o OUTPUT_DIR] [--no-rich] [--debug]

options:
  -h, --help            Show help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Directory to save downloaded chats (default: ~/TeamsDownloads)
  --no-rich             Disable rich formatting
  --debug               Enable debug output
```

### Workflow

1. **Environment Check**
   - Detects platform and Teams installation
   - Validates user is logged into Teams

2. **Chat Selection**
   - Lists available direct chats, group chats, and channels
   - Provides interactive selection interface

3. **Download Configuration**
   - Output format selection (JSON/TEXT/HTML/MARKDOWN)
   - Message limit configuration (all or N most recent)
   - Date range filtering (optional)

4. **Output**
   - Downloads messages with progress indicator
   - Saves to specified location with timestamp

### Output Formats

| Format | Description | Best For |
|--------|-------------|----------|
| JSON | Raw structured data | Data processing or import to other tools |
| TEXT | Plain text with timestamps | Simple viewing and archiving |
| HTML | Formatted for browsers | Web viewing with formatting |
| MARKDOWN | Clean documentation format | Readable documentation and conversion |

### Examples

**Basic usage:**
```bash
teamschatgrab
```

**Custom output location:**
```bash
teamschatgrab --output-dir ~/Desktop/TeamsBackup
```

**Troubleshooting:**
```bash
teamschatgrab --debug
```

## Development

### Environment Setup

```bash
# Clone repository and install development dependencies
git clone https://github.com/username/teamschatgrab.git
cd teamschatgrab
poetry install
```

### Development Commands

| Command | Purpose |
|---------|---------|
| `poetry run black src tests` | Format code |
| `poetry run flake8 src tests` | Run linting |
| `poetry run mypy src` | Type checking |
| `poetry run pytest` | Run all tests |
| `poetry run pytest tests/unit/test_api.py` | Run specific tests |
| `poetry run pytest --cov=teamschatgrab` | Run tests with coverage |

### Project Structure

```
src/teamschatgrab/           # Core application code
├── __main__.py              # Entry point
├── app.py                   # Main application logic
├── api.py                   # Teams API interface
├── auth.py                  # Authentication utilities 
├── platform_detection.py    # Cross-platform support
├── storage.py               # Message storage handling
└── ui.py                    # User interface

tests/                       # Test suite
├── unit/                    # Unit tests for each module
└── architecture/            # Architecture verification tests
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No logged-in Teams user found" | Ensure Teams is running and you're logged in |
| "Teams data path not found" | Verify Teams is installed in the standard location |
| "Authentication error" | Restart Teams and log in again |
| "Failed to fetch chats" | Check network connection and Teams connectivity |

### Platform-Specific Notes

- **Windows**: Teams data typically at `%APPDATA%\Microsoft\Teams`
- **macOS**: Teams data typically at `~/Library/Application Support/Microsoft/Teams`
- **WSL**: Teams data accessed via `/mnt/c/Users/[username]/AppData/Roaming/Microsoft/Teams`

### Advanced Debugging

```bash
teamschatgrab --debug
```

## Limitations

- Requires an active Teams session
- Some Teams API endpoints may change with Teams updates
- Attachment handling is limited
- Does not support meeting chat history

## License

MIT License

Copyright (C) 2025 Eric C. Mumford (@heymumford)