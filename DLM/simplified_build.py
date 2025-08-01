#!/usr/bin/env python
import os
import sys
import shutil
import subprocess
import argparse

def build_executable(debug=False):
    print("Building PyDownload Manager executable...")
    
    # Clean previous build
    print("Cleaning previous build...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("PyDownloadManager.spec"):
        os.remove("PyDownloadManager.spec")
    
    # Determine path separator based on OS
    path_separator = ";" if sys.platform == "win32" else ":"
    
    # Basic PyInstaller command
    pyinstaller_command = [
        "pyinstaller",
        "--name=PyDownloadManager",
        "--onefile",
        "--clean",
    ]
    
    # Add icon
    icon_path = os.path.join("browser_extensions", "chrome", "icons", "icon128.png")
    pyinstaller_command.append(f"--icon={icon_path}")
    
    # Add console window for debugging if requested
    if not debug:
        pyinstaller_command.append("--windowed")
    else:
        print("Building in debug mode with console window...")
    
    # Add hidden imports
    pyinstaller_command.extend([
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.sip",
    ])
    
    # Add data files
    pyinstaller_command.append(f"--add-data=browser_extensions{path_separator}browser_extensions")
    
    # Add essential PyQt5 DLLs
    essential_dlls = [
        "Qt5Core.dll",
        "Qt5Gui.dll",
        "Qt5Widgets.dll",
        "Qt5Network.dll",
        "msvcp140.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll"
    ]
    
    try:
        import PyQt5
        pyqt_dir = os.path.dirname(PyQt5.__file__)
        qt_bin_dir = os.path.join(pyqt_dir, 'Qt5', 'bin')
        if os.path.exists(qt_bin_dir):
            for dll in essential_dlls:
                dll_path = os.path.join(qt_bin_dir, dll)
                if os.path.exists(dll_path):
                    pyinstaller_command.append(f"--add-binary={dll_path}{path_separator}.")
                    print(f"Adding {dll}")
                else:
                    print(f"Warning: Could not find {dll}")
    except Exception as e:
        print(f"Warning: Could not locate PyQt5 DLLs: {e}")
    
    # Disable UPX compression
    pyinstaller_command.append("--noupx")
    
    # Add entry point
    pyinstaller_command.append("main.py")
    
    # Run PyInstaller
    print("Running PyInstaller...")
    try:
        subprocess.run(pyinstaller_command, check=True)
        print("\nBuild completed successfully!")
        print("\nNotes on the executable:")
        print("1. The executable includes all necessary files, including browser extensions")
        print("2. When installing the Chrome extension, it will extract the files to %LOCALAPPDATA%\\PyDownloadManager")
        print("3. Native messaging host registration will use the executable path automatically")
        print("4. Distribute the single PyDownloadManager.exe file to end users")
        print("5. Users will need to manually install the Chrome extension from the extracted location")
        print("6. The executable is self-contained and does not require additional files")
        print("7. If users encounter 'ordinal 380' errors, direct them to run the install_vcredist.bat script")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Build PyDownload Manager executable")
    parser.add_argument("--debug", action="store_true", help="Build with console window for debugging")
    args = parser.parse_args()
    
    # Install required packages
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=4.5.0"], check=True)
    
    # Build the executable
    success = build_executable(debug=args.debug)
    
    if success:
        print("\nBuild completed successfully!")
        print(f"Executable is located at: {os.path.abspath(os.path.join('dist', 'PyDownloadManager.exe'))}")
    else:
        print("\nBuild failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()