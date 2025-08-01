@echo off
echo Building PyDownload Manager executable...
echo.

if "%1"=="--debug" (
    echo Debug mode enabled
    python build_exe.py --debug
) else (
    python build_exe.py
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build successful! The executable is in the dist folder.
    echo You can now distribute PyDownloadManager.exe as a standalone application.
) else (
    echo Build failed. Please check the error messages above.
)

pause