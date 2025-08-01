import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui import DownloadManagerGUI


def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PyDownload Manager")
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set application icon
    # app.setWindowIcon(QIcon("icon.png"))  # Uncomment and add icon file if available
    
    # Create and show the main window
    main_window = DownloadManagerGUI()
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()