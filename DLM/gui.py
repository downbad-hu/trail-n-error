import sys
import os
import time
import threading
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAction,
                             QMessageBox, QSystemTrayIcon, QStyle, QTabWidget, QComboBox,
                             QSpinBox, QCheckBox, QGroupBox, QFormLayout, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl, QThread, QSize
from PyQt5.QtGui import QIcon, QClipboard, QDesktopServices

from download_engine import DownloadEngine, DownloadStatus
from browser_integration import BrowserIntegration


class ClipboardMonitor(QThread):
    url_detected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard = QApplication.clipboard()
        self.last_text = self.clipboard.text()
        self.running = True
    
    def run(self):
        while self.running:
            current_text = self.clipboard.text()
            if current_text != self.last_text:
                self.last_text = current_text
                # Check if text is a URL
                if current_text.startswith(('http://', 'https://', 'ftp://')):
                    self.url_detected.emit(current_text)
            time.sleep(0.5)
    
    def stop(self):
        self.running = False


class DownloadItemWidget(QWidget):
    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top row: Filename and status
        top_layout = QHBoxLayout()
        self.filename_label = QLabel(self.download_item.filename)
        self.filename_label.setStyleSheet("font-weight: bold;")
        self.status_label = QLabel(self.download_item.status.value)
        
        top_layout.addWidget(self.filename_label)
        top_layout.addStretch()
        top_layout.addWidget(self.status_label)
        
        # Middle row: Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.download_item.progress))
        
        # Bottom row: Size, speed, and buttons
        bottom_layout = QHBoxLayout()
        self.size_label = QLabel(f"0 MB / {self.format_size(self.download_item.total_size)}")
        self.speed_label = QLabel("0 KB/s")
        
        self.pause_resume_btn = QPushButton("Pause")
        self.cancel_btn = QPushButton("Cancel")
        
        bottom_layout.addWidget(self.size_label)
        bottom_layout.addWidget(self.speed_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.pause_resume_btn)
        bottom_layout.addWidget(self.cancel_btn)
        
        # Add all rows to main layout
        layout.addLayout(top_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(bottom_layout)
        
        # Set fixed height for the widget
        self.setFixedHeight(100)
    
    def update_info(self):
        self.filename_label.setText(self.download_item.filename)
        self.status_label.setText(self.download_item.status.value)
        self.progress_bar.setValue(int(self.download_item.progress))
        self.size_label.setText(
            f"{self.format_size(self.download_item.downloaded_size)} / {self.format_size(self.download_item.total_size)}"
        )
        self.speed_label.setText(self.format_speed(self.download_item.speed))
        
        # Update button text based on status
        if self.download_item.status == DownloadStatus.PAUSED:
            self.pause_resume_btn.setText("Resume")
        elif self.download_item.status == DownloadStatus.DOWNLOADING:
            self.pause_resume_btn.setText("Pause")
        
        # Disable buttons if completed or error
        if self.download_item.status in [DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELED]:
            self.pause_resume_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
    
    @staticmethod
    def format_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    @staticmethod
    def format_speed(speed_bytes):
        return f"{DownloadItemWidget.format_size(speed_bytes)}/s"


class DownloadManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_engine = DownloadEngine(max_concurrent_downloads=3, max_threads_per_download=5)
        self.download_widgets = {}
        self.clipboard_monitor = None
        self.browser_integration = BrowserIntegration(self)
        self.init_ui()
        self.register_callbacks()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_download_items)
        self.update_timer.start(500)  # Update every 500ms
    
    def init_ui(self):
        self.setWindowTitle("PyDownload Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Downloads tab
        downloads_tab = QWidget()
        downloads_layout = QVBoxLayout(downloads_tab)
        
        # URL input area
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter download URL here")
        browse_btn = QPushButton("Browse")
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.start_download)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(browse_btn)
        url_layout.addWidget(download_btn)
        
        downloads_layout.addLayout(url_layout)
        
        # Downloads area
        self.downloads_container = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_container)
        self.downloads_layout.setAlignment(Qt.AlignTop)
        
        # Create a scroll area for downloads
        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.addWidget(self.downloads_container)
        scroll_layout.addStretch()
        
        downloads_layout.addWidget(scroll_area)
        
        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        self.save_path_input = QLineEdit(os.path.expanduser("~/Downloads"))
        browse_save_path_btn = QPushButton("Browse")
        browse_save_path_btn.clicked.connect(self.browse_save_path)
        save_path_layout = QHBoxLayout()
        save_path_layout.addWidget(self.save_path_input)
        save_path_layout.addWidget(browse_save_path_btn)
        
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(1, 10)
        self.max_downloads_spin.setValue(3)
        self.max_downloads_spin.valueChanged.connect(self.update_max_downloads)
        
        self.clipboard_monitor_check = QCheckBox("Monitor clipboard for URLs")
        self.clipboard_monitor_check.setChecked(True)
        self.clipboard_monitor_check.stateChanged.connect(self.toggle_clipboard_monitor)
        
        general_layout.addRow("Default save path:", save_path_layout)
        general_layout.addRow("Max concurrent downloads:", self.max_downloads_spin)
        general_layout.addRow("", self.clipboard_monitor_check)
        
        # Connection settings group
        connection_group = QGroupBox("Connection Settings")
        connection_layout = QFormLayout(connection_group)
        
        self.threads_per_download_spin = QSpinBox()
        self.threads_per_download_spin.setRange(1, 16)
        self.threads_per_download_spin.setValue(5)
        self.threads_per_download_spin.valueChanged.connect(self.update_threads_per_download)
        
        self.speed_limit_check = QCheckBox("Limit download speed")
        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(50, 10000)
        self.speed_limit_spin.setValue(1000)
        self.speed_limit_spin.setSuffix(" KB/s")
        self.speed_limit_spin.setEnabled(False)
        self.speed_limit_check.stateChanged.connect(self.toggle_speed_limit)
        
        connection_layout.addRow("Threads per download:", self.threads_per_download_spin)
        connection_layout.addRow("Speed limit:", self.speed_limit_check)
        connection_layout.addRow("", self.speed_limit_spin)
        
        settings_layout.addWidget(general_group)
        settings_layout.addWidget(connection_group)
        settings_layout.addStretch()
        
        # Browser Integration tab
        browser_tab = QWidget()
        browser_layout = QVBoxLayout(browser_tab)
        
        # Browser integration group
        browser_group = QGroupBox("Browser Integration")
        browser_group_layout = QVBoxLayout(browser_group)
        
        # Chrome extension section
        chrome_section = QGroupBox("Chrome Extension")
        chrome_layout = QVBoxLayout(chrome_section)
        
        chrome_status_label = QLabel("Extension Status: Not installed")
        install_chrome_btn = QPushButton("Install Chrome Extension")
        install_chrome_btn.clicked.connect(self.install_chrome_extension)
        
        chrome_layout.addWidget(chrome_status_label)
        chrome_layout.addWidget(install_chrome_btn)
        
        # Server status section
        server_section = QGroupBox("Integration Server")
        server_layout = QVBoxLayout(server_section)
        
        server_status_label = QLabel("Server Status: Not running")
        self.server_toggle_btn = QPushButton("Start Server")
        self.server_toggle_btn.clicked.connect(self.toggle_integration_server)
        
        server_port_layout = QHBoxLayout()
        server_port_label = QLabel("Server Port:")
        self.server_port_spin = QSpinBox()
        self.server_port_spin.setRange(1024, 65535)
        self.server_port_spin.setValue(8765)
        server_port_layout.addWidget(server_port_label)
        server_port_layout.addWidget(self.server_port_spin)
        server_port_layout.addStretch()
        
        server_layout.addWidget(server_status_label)
        server_layout.addLayout(server_port_layout)
        server_layout.addWidget(self.server_toggle_btn)
        
        # Add sections to browser group
        browser_group_layout.addWidget(chrome_section)
        browser_group_layout.addWidget(server_section)
        
        # Help section
        help_group = QGroupBox("Help")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel("Browser integration allows you to intercept downloads directly from your browser. "
                          "Install the extension and start the integration server to enable this feature.")
        help_text.setWordWrap(True)
        
        help_layout.addWidget(help_text)
        
        # Add groups to browser tab
        browser_layout.addWidget(browser_group)
        browser_layout.addWidget(help_group)
        browser_layout.addStretch()
        
        # Add tabs to tab widget
        tab_widget.addTab(downloads_tab, "Downloads")
        tab_widget.addTab(settings_tab, "Settings")
        tab_widget.addTab(browser_tab, "Browser Integration")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Start clipboard monitor
        self.start_clipboard_monitor()
    
    def register_callbacks(self):
        """Register callbacks with the download engine"""
        self.download_engine.register_callback('added', self.on_download_added)
        self.download_engine.register_callback('started', self.on_download_started)
        self.download_engine.register_callback('progress', self.on_download_progress)
        self.download_engine.register_callback('paused', self.on_download_paused)
        self.download_engine.register_callback('resumed', self.on_download_resumed)
        self.download_engine.register_callback('completed', self.on_download_completed)
        self.download_engine.register_callback('error', self.on_download_error)
        self.download_engine.register_callback('canceled', self.on_download_canceled)
    
    def start_download(self):
        """Start a new download"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL")
            return
        
        save_path = self.save_path_input.text()
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create save directory: {str(e)}")
                return
        
        download_id = self.download_engine.add_download(url, save_path)
        self.url_input.clear()
        self.statusBar().showMessage(f"Download added: {url}")
    
    def on_download_added(self, download_item):
        """Callback when a download is added"""
        # Create a widget for this download
        widget = DownloadItemWidget(download_item)
        widget.pause_resume_btn.clicked.connect(lambda: self.toggle_pause_resume(download_item.id))
        widget.cancel_btn.clicked.connect(lambda: self.cancel_download(download_item.id))
        
        # Add to layout and store reference
        self.downloads_layout.insertWidget(0, widget)
        self.download_widgets[download_item.id] = widget
    
    def on_download_started(self, download_item):
        """Callback when a download is started"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
    
    def on_download_progress(self, download_item):
        """Callback when download progress is updated"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
    
    def on_download_paused(self, download_item):
        """Callback when a download is paused"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
    
    def on_download_resumed(self, download_item):
        """Callback when a download is resumed"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
    
    def on_download_completed(self, download_item):
        """Callback when a download is completed"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
            self.statusBar().showMessage(f"Download completed: {download_item.filename}")
    
    def on_download_error(self, download_item):
        """Callback when a download encounters an error"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
            self.statusBar().showMessage(f"Download error: {download_item.error_message}")
    
    def on_download_canceled(self, download_item):
        """Callback when a download is canceled"""
        if download_item.id in self.download_widgets:
            self.download_widgets[download_item.id].update_info()
    
    def toggle_pause_resume(self, download_id):
        """Toggle pause/resume for a download"""
        download_item = self.download_engine.get_download_info(download_id)
        if download_item:
            if download_item.status == DownloadStatus.DOWNLOADING:
                self.download_engine.pause_download(download_id)
            elif download_item.status == DownloadStatus.PAUSED:
                self.download_engine.resume_download(download_id)
    
    def cancel_download(self, download_id):
        """Cancel a download"""
        self.download_engine.cancel_download(download_id)
    
    def update_download_items(self):
        """Update all download items"""
        for download_id, widget in self.download_widgets.items():
            widget.update_info()
    
    def browse_save_path(self):
        """Browse for default save path"""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.save_path_input.text())
        if directory:
            self.save_path_input.setText(directory)
    
    def update_max_downloads(self):
        """Update maximum concurrent downloads"""
        self.download_engine.max_concurrent_downloads = self.max_downloads_spin.value()
    
    def update_threads_per_download(self):
        """Update maximum threads per download"""
        self.download_engine.max_threads_per_download = self.threads_per_download_spin.value()
    
    def toggle_speed_limit(self, state):
        """Toggle speed limit"""
        self.speed_limit_spin.setEnabled(state == Qt.Checked)
        # TODO: Implement speed limiting in download engine
    
    def start_clipboard_monitor(self):
        """Start the clipboard monitor thread"""
        if self.clipboard_monitor is None and self.clipboard_monitor_check.isChecked():
            self.clipboard_monitor = ClipboardMonitor()
            self.clipboard_monitor.url_detected.connect(self.on_url_detected)
            self.clipboard_monitor.start()
    
    def stop_clipboard_monitor(self):
        """Stop the clipboard monitor thread"""
        if self.clipboard_monitor is not None:
            self.clipboard_monitor.stop()
            self.clipboard_monitor.wait()
            self.clipboard_monitor = None
    
    def toggle_clipboard_monitor(self, state):
        """Toggle clipboard monitoring"""
        if state == Qt.Checked:
            self.start_clipboard_monitor()
        else:
            self.stop_clipboard_monitor()
    
    def on_url_detected(self, url):
        """Handle detected URL from clipboard"""
        # Ask user if they want to download this URL
        reply = QMessageBox.question(
            self, "URL Detected", f"Do you want to download this URL?\n\n{url}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.url_input.setText(url)
            self.start_download()
    
    def install_chrome_extension(self):
        """Install Chrome extension"""
        try:
            # Install the extension
            extension_path = self.browser_integration.install_chrome_extension()
            
            # Show success message with instructions
            QMessageBox.information(
                self,
                "Extension Installed",
                f"Chrome extension has been installed to:\n{extension_path}\n\n"
                "To complete installation:\n"
                "1. Open Chrome and go to chrome://extensions\n"
                "2. Enable 'Developer mode' (top-right toggle)\n"
                "3. Click 'Load unpacked' and select the extension folder\n"
                "4. Start the integration server in this app"
            )
            
            # Open Chrome extensions page
            webbrowser.open('chrome://extensions/')
            
        except Exception as e:
            QMessageBox.warning(self, "Installation Error", f"Failed to install extension: {str(e)}")
    
    def toggle_integration_server(self):
        """Toggle the integration server on/off"""
        if self.browser_integration.is_server_running():
            # Stop the server
            self.browser_integration.stop_server()
            self.server_toggle_btn.setText("Start Server")
            self.statusBar().showMessage("Browser integration server stopped")
        else:
            # Start the server
            port = self.server_port_spin.value()
            try:
                self.browser_integration.start_server(port)
                self.server_toggle_btn.setText("Stop Server")
                self.statusBar().showMessage(f"Browser integration server running on port {port}")
            except Exception as e:
                QMessageBox.warning(self, "Server Error", f"Failed to start server: {str(e)}")
    
    def add_download_from_browser(self, url, filename=None, referrer=None):
        """Add a download from browser integration"""
        save_path = self.save_path_input.text()
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path, exist_ok=True)
            except Exception as e:
                self.statusBar().showMessage(f"Error creating save directory: {str(e)}")
                return False
        
        # Add the download
        download_id = self.download_engine.add_download(url, save_path, filename, referrer)
        self.statusBar().showMessage(f"Download added from browser: {url}")
        return True
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop clipboard monitor
        self.stop_clipboard_monitor()
        
        # Stop browser integration server
        if self.browser_integration.is_server_running():
            self.browser_integration.stop_server()
        
        # Shutdown download engine
        self.download_engine.shutdown()
        
        # Accept the close event
        event.accept()