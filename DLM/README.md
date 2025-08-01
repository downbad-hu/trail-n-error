# PyDownloadManager

A GUI-based download manager similar to Internet Download Manager (IDM) built with Python and PyQt5.

## Features

- Multi-threaded downloading with parallel connections for faster downloads
- Pause and resume support
- Download progress bar with percentage
- Ability to handle large files
- Download queue management
- Clean, user-friendly interface
- Browser integration with Chrome extension

### Optional Features

- Clipboard auto-detect URLs
- Speed limit control
- Retry on failure
- Native browser integration

## Requirements

- Python 3.6+
- PyQt5
- requests
- threading

## Project Structure

```
├── main.py                 # Application entry point
├── download_engine.py      # Core download functionality
├── gui.py                  # PyQt5 GUI implementation
├── utils.py                # Utility functions
└── README.md               # Project documentation
```

## Usage

Run the application with:

```
python main.py
```

## Building Executable

To build a standalone executable:

1. Make sure you have all requirements installed:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Run the build script:
   ```
   python build_exe.py
   ```
   
   Or on Windows, simply double-click the `build_exe.bat` file.
   
   For debugging purposes, you can build with console output enabled:
   ```
   python build_exe.py --debug
   ```
   Or on Windows:
   ```
   build_exe.bat --debug
   ```

3. The executable will be created in the `dist` folder.

### Notes on Executable Distribution

- The executable includes all necessary files, including browser extensions
- When installing the Chrome extension, it will extract files to a temporary location
- Native messaging host registration will use the executable path automatically
- Distribute the single `PyDownloadManager.exe` file to end users

## Troubleshooting

If you encounter issues such as "The ordinal 380 could not be located" error or other problems, please refer to the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide for solutions.