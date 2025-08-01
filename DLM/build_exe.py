#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform

def build_executable(debug=False):
    print("Building PyDownload Manager executable...")
    
    # Install required packages
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=4.5.0"])
    
    # Create build directory if it doesn't exist
    if not os.path.exists("build"):
        os.makedirs("build")
    
    # Clean previous build if exists
    dist_dir = os.path.join(os.getcwd(), "dist")
    if os.path.exists(dist_dir):
        print("Cleaning previous build...")
        shutil.rmtree(dist_dir)
    
    # Build executable with PyInstaller
    print("Running PyInstaller...")
    
    # Handle platform-specific path separator for --add-data
    path_separator = ';' if platform.system() == 'Windows' else ':'
    
    # Add data files to include in the executable
    data_files = [
        ("browser_extensions", "browser_extensions"),
    ]
    
    # Add binary files to include in the executable
    # This helps with missing DLL issues like ordinal 380 errors
    binary_files = []
    
    # Try to locate PyQt5 DLLs if they exist
    try:
        import PyQt5
        pyqt_dir = os.path.dirname(PyQt5.__file__)
        qt_bin_dir = os.path.join(pyqt_dir, 'Qt5', 'bin')
        if os.path.exists(qt_bin_dir):
            for dll in os.listdir(qt_bin_dir):
                if dll.lower().endswith('.dll'):
                    binary_files.append((os.path.join(qt_bin_dir, dll), '.'))
    except Exception as e:
        print(f"Warning: Could not locate PyQt5 DLLs: {e}")
    
    
    # Convert data files to PyInstaller format
    add_data_params = []
    for src, dst in data_files:
        add_data_params.append(f"--add-data={src}{path_separator}{dst}")
        
    # Convert binary files to PyInstaller format
    add_binary_params = []
    for src, dst in binary_files:
        add_binary_params.append(f"--add-binary={src}{path_separator}{dst}")
    
    # Use platform-specific path for icon
    icon_path = os.path.join('browser_extensions', 'chrome', 'icons', 'icon128.png')
    
    # Basic PyInstaller command
    pyinstaller_command = [
        "pyinstaller",
        "--name=PyDownloadManager",
        "--onefile",   # Single executable file
        "--clean",     # Clean PyInstaller cache
        f"--icon={icon_path}",  # Use extension icon
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.sip",
    ]
    
    # Add windowed mode (no console) unless debug mode is enabled
    if not debug:
        pyinstaller_command.append("--windowed")  # No console window
    else:
        print("Building in debug mode with console window...")
    
    
    # Add data files
    pyinstaller_command.extend(add_data_params)
    
    # Add binary files
    pyinstaller_command.extend(add_binary_params)
    
    # Add additional options to help with DLL issues
    pyinstaller_command.append("--noupx")  # Disable UPX compression which can cause issues
    
    # Add entry point
    pyinstaller_command.append("main.py")
    
    subprocess.check_call(pyinstaller_command)
    
    print("\nBuild completed! Executable is located in the 'dist' folder.")
    print("\nNotes for using the executable:")
    print("1. The browser extensions are bundled with the executable")
    print("2. When installing the Chrome extension, it will extract the files to %LOCALAPPDATA%\\PyDownloadManager")
    print("3. Native messaging host registration will use the executable path automatically")
    print("4. The executable can be distributed to other computers without additional dependencies")
    print("5. Users will need to install the Chrome extension manually from the extracted location")
    print("6. If users encounter 'ordinal 380' errors, direct them to run the install_vcredist.bat script")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build PyDownload Manager executable")
    parser.add_argument("--debug", action="store_true", help="Build with console for debugging")
    args = parser.parse_args()
    
    build_executable(debug=args.debug)