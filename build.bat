@echo off
echo ====================================================
echo           Teams Chat Grabber Build Script           
echo ====================================================

REM Check if Poetry is installed
where poetry >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Poetry is not installed. Please install it first:
    echo pip install poetry
    exit /b 1
)

echo.
echo =^> Installing dependencies
poetry install

echo.
echo =^> Formatting code with Black
poetry run black src tests

echo.
echo =^> Running Flake8 linting
poetry run flake8 src tests || (
    echo Linting issues found but continuing...
)

echo.
echo =^> Running MyPy type checking
poetry run mypy src || (
    echo Type issues found but continuing...
)

echo.
echo =^> Running tests
poetry run pytest tests -v || (
    echo Tests failed!
    exit /b 1
)

echo.
echo =^> Building package
poetry build

echo.
echo Build completed successfully!

echo.
echo ====================================================
echo                 HOW TO USE THE APP                  
echo ====================================================
echo.
echo To run the application:
echo.
echo 1. Option 1: Run with a single command:
echo    build.bat run
echo.
echo 2. Option 2: Manually activate environment:
echo    for /f "tokens=*" %%i in ('poetry env info --path') do set VENV_PATH=%%i
echo    call !VENV_PATH!\Scripts\activate.bat
echo    teamschatgrab
echo.
echo 3. Run with options:
echo    teamschatgrab --output-dir C:\Users\YourName\Desktop\TeamsChats
echo.
echo 4. Follow the interactive prompts to:
echo    - Select a chat or channel to download
echo    - Choose output format (JSON, Text, HTML, or Markdown)
echo    - Specify number of messages to download
echo    - Set date range (optional)
echo.
echo 5. To download a chat from a specific date:
echo    When prompted "Filter by date range?", select Yes
echo    Enter the start date in YYYY-MM-DD format
echo    Leave the end date empty to use today's date
echo.
echo 6. The downloaded chat will be stored in:
echo    %USERPROFILE%\TeamsDownloads\  (default location)
echo    Or your custom location if specified with --output-dir
echo.
echo ====================================================

REM Check if run argument is provided
if "%1"=="run" (
    echo.
    echo =^> Activating virtual environment and launching application
    
    REM Enable delayed expansion for variables set inside loops
    setlocal EnableDelayedExpansion
    
    REM Get the virtual environment path
    for /f "tokens=*" %%i in ('poetry env info --path') do set VENV_PATH=%%i
    
    if "!VENV_PATH!"=="" (
        echo Virtual environment not found. Creating one...
        poetry install
        for /f "tokens=*" %%i in ('poetry env info --path') do set VENV_PATH=%%i
    )
    
    REM Activate virtual environment and run the application
    echo Activating virtual environment...
    call "!VENV_PATH!\Scripts\activate.bat"
    echo Launching application...
    
    REM Pass any additional arguments after "run" to the application
    if "%2"=="" (
        teamschatgrab
    ) else (
        REM Build the arguments string
        set ARGS=
        set ARGCOUNT=0
        for %%x in (%*) do (
            set /a ARGCOUNT+=1
            if !ARGCOUNT! GTR 1 set ARGS=!ARGS! %%x
        )
        teamschatgrab !ARGS:~1!
    )
    endlocal
)