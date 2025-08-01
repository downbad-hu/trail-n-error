# Troubleshooting PyDownload Manager

## Executable Closes Immediately After Opening

If the PyDownloadManager.exe opens briefly and then closes immediately:

1. Run the included `debug_run.bat` script, which will capture any error messages and display them.

2. If no error messages are displayed, it's likely a missing dependency issue. Try running the `install_vcredist.bat` script to install the required Visual C++ Redistributable packages.

3. As an alternative, try using the Python-based distribution created with `build_with_pyqt.py` instead of the standalone executable.

## "The ordinal 380 could not be located" Error

If you encounter the error message "The ordinal 380 could not be located" when running the PyDownloadManager.exe, follow these steps to resolve it:

### Solution 1: Install Visual C++ Redistributable Packages

This error typically occurs when the required Visual C++ Redistributable packages are missing on your system.

1. Run the included `install_vcredist.bat` script, which will automatically download and install the necessary packages.

2. Alternatively, you can manually download and install the Visual C++ Redistributable packages from Microsoft's website:
   - [Visual C++ Redistributable for Visual Studio 2015-2019 (x86)](https://aka.ms/vs/16/release/vc_redist.x86.exe)
   - [Visual C++ Redistributable for Visual Studio 2015-2019 (x64)](https://aka.ms/vs/16/release/vc_redist.x64.exe)

3. Install both the x86 (32-bit) and x64 (64-bit) versions for maximum compatibility.

### Solution 2: Rebuild with Enhanced DLL Support

If installing the Visual C++ Redistributable packages doesn't resolve the issue, you can rebuild the executable with enhanced DLL support:

1. Make sure you have the source code and Python environment set up.

2. Run the build script with debug mode enabled:
   ```
   python build_exe.py --debug
   ```

3. The updated build includes additional DLL dependencies and disables UPX compression, which can help resolve the issue.

### Solution 3: Check for Antivirus Interference

Sometimes antivirus software can interfere with the execution of PyInstaller-bundled applications:

1. Temporarily disable your antivirus software.
2. Try running the application again.
3. If it works, add an exception for PyDownloadManager.exe in your antivirus settings.

### Solution 4: Run in a Clean Environment

1. Close all other applications.
2. Restart your computer.
3. Try running PyDownloadManager.exe again without starting any other applications.

## Other Common Issues

### Browser Extension Not Working

If the Chrome extension is not working properly:

1. Make sure the integration server is running in PyDownload Manager.
2. Verify that the extension is properly installed in Chrome.
3. Check Chrome's extension settings to ensure it has the necessary permissions.
4. Try reinstalling the extension from the %LOCALAPPDATA%\PyDownloadManager\chrome_extension directory.

### Downloads Not Being Intercepted

If downloads are not being intercepted by PyDownload Manager:

1. Make sure the browser integration server is running.
2. Check the extension settings by clicking on the extension icon in Chrome.
3. Verify that the file types you're trying to download are included in the extension's settings.
4. Ensure the minimum file size setting is appropriate for your downloads.

### Need Further Help?

If you continue to experience issues, please report them on the project's issue tracker with detailed information about your system and the specific error messages you're encountering.