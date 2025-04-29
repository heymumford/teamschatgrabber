# Teams Chat Grabber: Quick Start Guide

This guide provides the fastest way to get started with Teams Chat Grabber.

## Installation (First Time Only)

### Step 1: Install Poetry

**On macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**On Windows:**
```bash
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Step 2: Setup the Application

**On macOS/Linux:**
```bash
./build.sh
```

**On Windows:**
```bash
build.bat
```

## Usage

### Step 1: Ensure Teams is Running
Make sure Microsoft Teams is open and you're logged in.

### Step 2: Run the Application

#### Option 1: One-Command Launch (Recommended)

**On macOS/Linux:**
```bash
./build.sh run
```

**On Windows:**
```bash
build.bat run
```

#### Option 2: Manual Activation

**On macOS/Linux:**
```bash
source $(poetry env info --path)/bin/activate
teamschatgrab
```

**On Windows:**
```
# Run this in Command Prompt
for /f "tokens=*" %i in ('poetry env info --path') do set VENV_PATH=%i
call %VENV_PATH%\Scripts\activate.bat
teamschatgrab
```

### Step 3: Select a Chat or Channel

When you run the application, it will:
1. Detect your platform (macOS or Windows)
2. Find your Teams installation and logged-in account
3. Show a list of available chats and channels

The selection screen displays:
- **Direct chats**: One-on-one conversations with other users
- **Group chats**: Multi-person conversations outside of Teams channels
- **Team channels**: Conversations within Teams channels

Use arrow keys to navigate, then press Enter to select a chat.

### Step 4: Configure Your Download

After selecting a chat, you'll be prompted to configure your download:

#### Output Format
Choose from multiple formats:
- **JSON**: Raw message data in structured format (best for data processing)
- **TEXT**: Simple plaintext format with timestamps and messages
- **HTML**: Formatted HTML for viewing in a browser
- **MARKDOWN**: Clean markdown format for easy reading

#### Message Limit
- Enter a number to limit the messages downloaded
- Leave empty to download all available messages

#### Date Range
You can filter messages by date:
1. Select "Yes" when asked "Filter by date range?"
2. Enter starting date in YYYY-MM-DD format (e.g., 2023-05-15)
   - Leave empty to include all messages from the beginning
3. Enter ending date in YYYY-MM-DD format
   - Leave empty to include all messages up to today

### Step 5: Find Your Downloaded Chat

After the download completes, the app will show the save location. By default, files are saved to:
- macOS: `~/TeamsDownloads/`
- Windows: `C:\Users\YourUsername\TeamsDownloads\`

Each chat is saved in its own directory with a timestamp.

## Common Options

- Download to a specific location:
  ```bash
  teamschatgrab --output-dir ~/Desktop/TeamsChatBackup
  ```

- Debug mode for troubleshooting:
  ```bash
  teamschatgrab --debug
  ```

- Basic terminal mode (without fancy formatting):
  ```bash
  teamschatgrab --no-rich
  ```

## Examples

### Example 1: Download Recent Messages
1. Run `teamschatgrab`
2. Select the chat you want to download
3. Choose your preferred format (e.g., TEXT)
4. Enter a limit (e.g., 100) to get only the most recent 100 messages
5. Select "No" when asked about date filtering

### Example 2: Download Messages from a Specific Time Period
1. Run `teamschatgrab`
2. Select the chat you want to download
3. Choose your preferred format (e.g., MARKDOWN)
4. Leave the message limit empty to get all messages
5. Select "Yes" when asked about date filtering
6. Enter start date (e.g., 2023-01-01)
7. Enter end date (e.g., 2023-01-31) to only get January 2023 messages

For more detailed information, see the full README.md file.

---

Copyright (C) 2025 Eric C. Mumford (@heymumford)
MIT License