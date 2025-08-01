@echo off
echo PyDownload Manager - Setup
echo ============================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python is installed. Installing required packages...
echo.

REM Install required packages
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install required packages.
    echo Please make sure you have internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo.
echo You can now run PyDownloadManager by double-clicking on PyDownloadManager.bat
echo.

REM Ask if user wants to run the application now
set /p RUNAPP=Do you want to run PyDownload Manager now? (Y/N): 

if /i "%RUNAPP%"=="Y" (
    echo.
    echo Starting PyDownload Manager...
    start PyDownloadManager.bat
) else (
    echo.
    echo You can run PyDownload Manager later by double-clicking on PyDownloadManager.bat
)

echo.
pause