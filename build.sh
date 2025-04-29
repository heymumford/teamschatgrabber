#!/usr/bin/env bash
set -e

# Colors for output
# Check if terminal supports colors
if [ -t 1 ] && [ -n "$(tput colors 2>/dev/null || echo 0)" ] && [ "$(tput colors)" -ge 8 ]; then
    USE_COLORS=true
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    RED="\033[0;31m"
    BLUE="\033[0;34m"
    RESET="\033[0m"
else
    USE_COLORS=false
    GREEN=""
    YELLOW=""
    RED=""
    BLUE=""
    RESET=""
fi

echo -e "${BLUE}====================================================${RESET}"
echo -e "${BLUE}          Teams Chat Grabber Build Script           ${RESET}"
echo -e "${BLUE}====================================================${RESET}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Poetry is not installed. Please install it first:${RESET}"
    echo -e "${YELLOW}curl -sSL https://install.python-poetry.org | python3 -${RESET}"
    exit 1
fi

# Function to print section header
section() {
    echo -e "\n${BLUE}==>${RESET} ${GREEN}$1${RESET}"
}

# Install dependencies
section "Installing dependencies"
poetry install

# Format code with Black
section "Formatting code with Black"
poetry run black src tests

# Run linting with Flake8
section "Running Flake8 linting"
poetry run flake8 src tests || {
    echo -e "${YELLOW}Linting issues found but continuing...${RESET}"
}

# Run type checking with MyPy
section "Running MyPy type checking"
poetry run mypy src || {
    echo -e "${YELLOW}Type issues found but continuing...${RESET}"
}

# Run tests with Pytest
section "Running tests"
poetry run pytest tests -v || {
    echo -e "${RED}Tests failed!${RESET}"
    exit 1
}

# Build the package
section "Building package"
poetry build

echo -e "\n${GREEN}Build completed successfully!${RESET}"

# Print usage instructions
echo -e "\n${BLUE}====================================================${RESET}"
echo -e "${GREEN}                HOW TO USE THE APP                 ${RESET}"
echo -e "${BLUE}====================================================${RESET}"
echo -e ""
echo -e "${YELLOW}To run the application:${RESET}"
echo -e ""
echo -e "1. ${GREEN}Option 1: Run with a single command:${RESET}"
echo -e "   $ ./build.sh run"
echo -e ""
echo -e "2. ${GREEN}Option 2: Manually activate environment:${RESET}"
echo -e "   $ source \$(poetry env info --path)/bin/activate"
echo -e "   $ teamschatgrab"
echo -e ""
echo -e "3. ${YELLOW}Run with options:${RESET}"
echo -e "   $ teamschatgrab --output-dir ~/Desktop/TeamsChats"
echo -e "   "
echo -e "4. ${YELLOW}Follow the interactive prompts to:${RESET}"
echo -e "   - Select a chat or channel to download"
echo -e "   - Choose output format (JSON, Text, HTML, or Markdown)"
echo -e "   - Specify number of messages to download"
echo -e "   - Set date range (optional)"
echo -e "   "
echo -e "5. ${YELLOW}To download a chat from a specific date:${RESET}"
echo -e "   When prompted \"Filter by date range?\", select Yes"
echo -e "   Enter the start date in YYYY-MM-DD format"
echo -e "   Leave the end date empty to use today's date"
echo -e ""
echo -e "6. ${YELLOW}The downloaded chat will be stored in:${RESET}"
echo -e "   ~/TeamsDownloads/  (default location)"
echo -e "   Or your custom location if specified with --output-dir"
echo -e ""
echo -e "${BLUE}====================================================${RESET}"

# Check if run argument is provided
if [ "$1" = "run" ]; then
    section "Activating virtual environment and launching application"
    # Get the virtual environment path
    VENV_PATH=$(poetry env info --path)
    if [ -z "$VENV_PATH" ]; then
        echo -e "${RED}Virtual environment not found. Creating one...${RESET}"
        poetry install
        VENV_PATH=$(poetry env info --path)
    fi
    
    # Activate virtual environment and run the application
    echo -e "${GREEN}Activating virtual environment...${RESET}"
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}Launching application...${RESET}"
    
    # Pass any additional arguments after "run" to the application
    if [ "$#" -gt 1 ]; then
        teamschatgrab "${@:2}"
    else
        teamschatgrab
    fi
fi