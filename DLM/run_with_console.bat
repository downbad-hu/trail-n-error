@echo off
echo Running PyDownloadManager with console output...
echo.

REM Run the executable and pause after it completes or crashes
start /wait dist\PyDownloadManager.exe

echo.
echo If the application closed immediately, there was an error.
echo Check above for error messages.
echo.
pause