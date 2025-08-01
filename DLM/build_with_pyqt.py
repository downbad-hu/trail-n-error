#!/usr/bin/env python
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def build_executable(debug=False):
    print("Building PyDownload Manager executable using PyQt tools...")
    
    # Clean previous build
    print("Cleaning previous build...")
    dist_dir = Path("dist")
    build_dir = Path("build")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create output directories
    dist_dir.mkdir(exist_ok=True)
    app_dir = dist_dir / "PyDownloadManager"
    app_dir.mkdir(exist_ok=True)
    
    # Copy Python files
    print("Copying Python files...")
    python_files = [
        "main.py",
        "download_engine.py",
        "gui.py",
        "utils.py",
        "browser_integration.py"
    ]
    
    for file in python_files:
        if Path(file).exists():
            shutil.copy(file, app_dir)
    
    # Copy browser extensions
    print("Copying browser extensions...")
    extensions_dir = Path("browser_extensions")
    if extensions_dir.exists():
        dest_extensions_dir = app_dir / "browser_extensions"
        shutil.copytree(extensions_dir, dest_extensions_dir)
    
    # Create a launcher script
    print("Creating launcher script...")
    launcher_path = app_dir / "PyDownloadManager.bat"
    
    with open(launcher_path, "w") as f:
        f.write("@echo off\n")
        if debug:
            f.write("echo Running PyDownload Manager in debug mode...\n")
            f.write("python main.py\n")
            f.write("echo.\n")
            f.write("echo Application has exited. Press any key to close this window.\n")
            f.write("pause > nul\n")
        else:
            f.write("start pythonw main.py\n")
    
    # Create a README file
    readme_path = app_dir / "README.txt"
    with open(readme_path, "w") as f:
        f.write("PyDownload Manager\n")
        f.write("=================\n\n")
        f.write("This application requires Python 3.6+ and the following packages:\n")
        f.write("- PyQt5\n")
        f.write("- requests\n\n")
        f.write("To install the required packages, run:\n")
        f.write("pip install -r requirements.txt\n\n")
        f.write("To start the application:\n")
        f.write("1. Double-click on PyDownloadManager.bat\n\n")
        f.write("If you encounter any issues, please refer to TROUBLESHOOTING.md\n")
    
    # Copy requirements.txt
    if Path("requirements.txt").exists():
        shutil.copy("requirements.txt", app_dir)
    
    # Copy troubleshooting guide
    if Path("TROUBLESHOOTING.md").exists():
        shutil.copy("TROUBLESHOOTING.md", app_dir)
    
    # Copy install_vcredist.bat
    if Path("install_vcredist.bat").exists():
        shutil.copy("install_vcredist.bat", app_dir)
    
    # Create a ZIP file
    print("Creating ZIP archive...")
    shutil.make_archive("dist/PyDownloadManager", "zip", dist_dir, "PyDownloadManager")
    
    print("\nBuild completed successfully!")
    print(f"Application folder: {app_dir.absolute()}")
    print(f"ZIP archive: {Path('dist/PyDownloadManager.zip').absolute()}")
    print("\nNotes:")
    print("1. This build requires Python to be installed on the target system")
    print("2. Users will need to install the required packages using requirements.txt")
    print("3. The application can be started by running PyDownloadManager.bat")
    print("4. If users encounter issues, direct them to install_vcredist.bat and TROUBLESHOOTING.md")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Build PyDownload Manager using PyQt tools")
    parser.add_argument("--debug", action="store_true", help="Build with console output for debugging")
    args = parser.parse_args()
    
    # Build the application
    success = build_executable(debug=args.debug)
    
    if success:
        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()