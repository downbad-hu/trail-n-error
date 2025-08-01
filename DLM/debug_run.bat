@echo off
echo Running PyDownloadManager in debug mode...
echo This will capture any error messages when the application crashes
echo.

REM Create a temporary directory for logs if it doesn't exist
if not exist "%TEMP%\PyDownloadManager" mkdir "%TEMP%\PyDownloadManager"

REM Set the log file path
set LOG_FILE="%TEMP%\PyDownloadManager\debug_log.txt"

echo Logging output to: %LOG_FILE%
echo.

REM Run the executable with output redirection
echo Running application...
echo -------------------------------------------

REM Redirect both stdout and stderr to the log file and also display in console
dist\PyDownloadManager.exe > %LOG_FILE% 2>&1

echo -------------------------------------------
echo Application has exited.

REM Check if the log file has content
for %%A in (%LOG_FILE%) do set size=%%~zA
if %size% gtr 0 (
    echo Error messages found:
    echo -------------------------------------------
    type %LOG_FILE%
    echo -------------------------------------------
) else (
    echo No error messages were captured.
    echo The application may have crashed before producing any output.
)

echo.
echo If you need more detailed debugging:
echo 1. Try running the application from a command prompt
echo 2. Install the Visual C++ Redistributables using install_vcredist.bat
echo 3. Check TROUBLESHOOTING.md for more solutions
echo.

pause