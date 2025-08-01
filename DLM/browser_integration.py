import os
import json
import socket
import threading
import time
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('browser_integration')


class DownloadInterceptor(BaseHTTPRequestHandler):
    """HTTP request handler for intercepting download requests from browser extensions"""
    
    def __init__(self, *args, download_callback=None, **kwargs):
        self.download_callback = download_callback
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests from browser extensions"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            logger.info(f"Received download request: {data['url']}")
            
            # Call the download callback if available
            if self.download_callback and 'url' in data:
                self.download_callback(data['url'], data.get('filename', None), data.get('referrer', None))
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            else:
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Invalid request'}).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error processing download request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger instead of printing to stderr"""
        logger.debug("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


class BrowserIntegrationServer:
    """Server for handling browser extension integration"""
    
    def __init__(self, host='127.0.0.1', port=8765, download_callback=None):
        self.host = host
        self.port = port
        self.download_callback = download_callback
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Start the integration server"""
        if self.running:
            logger.warning("Server is already running")
            return False
        
        # Create a custom request handler with our callback
        handler = lambda *args, **kwargs: DownloadInterceptor(*args, download_callback=self.download_callback, **kwargs)
        
        try:
            self.server = HTTPServer((self.host, self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.running = True
            logger.info(f"Browser integration server started on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser integration server: {str(e)}")
            return False
    
    def stop(self):
        """Stop the integration server"""
        if not self.running:
            logger.warning("Server is not running")
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            logger.info("Browser integration server stopped")
    
    def is_running(self):
        """Check if the server is running"""
        return self.running


class NativeMessagingHost:
    """Native messaging host for deeper browser integration"""
    
    def __init__(self, download_callback=None):
        self.download_callback = download_callback
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the native messaging host"""
        if self.running:
            logger.warning("Native messaging host is already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Native messaging host started")
        return True
    
    def stop(self):
        """Stop the native messaging host"""
        if not self.running:
            logger.warning("Native messaging host is not running")
            return
        
        self.running = False
        logger.info("Native messaging host stopped")
    
    def _run(self):
        """Run the native messaging host"""
        try:
            # Native messaging protocol: first 4 bytes are message length, followed by the message
            while self.running:
                # Read the message length (first 4 bytes)
                length_bytes = sys.stdin.buffer.read(4)
                if not length_bytes:
                    break
                
                # Unpack message length as native-endian unsigned long
                message_length = int.from_bytes(length_bytes, byteorder='little')
                
                # Read the message of specified length
                message_bytes = sys.stdin.buffer.read(message_length)
                message = json.loads(message_bytes.decode('utf-8'))
                
                # Process the message
                if 'url' in message:
                    logger.info(f"Received download request via native messaging: {message['url']}")
                    if self.download_callback:
                        self.download_callback(message['url'], message.get('filename', None), message.get('referrer', None))
                
                # Send a response
                response = {'status': 'success'}
                response_bytes = json.dumps(response).encode('utf-8')
                response_length = len(response_bytes)
                sys.stdout.buffer.write(response_length.to_bytes(4, byteorder='little'))
                sys.stdout.buffer.write(response_bytes)
                sys.stdout.buffer.flush()
        
        except Exception as e:
            logger.error(f"Error in native messaging host: {str(e)}")
        finally:
            self.running = False


class BrowserIntegration:
    """Main class for browser integration"""
    
    def __init__(self, download_callback=None):
        self.download_manager_gui = download_callback
        self.server = BrowserIntegrationServer(download_callback=self._handle_download)
        self.native_host = NativeMessagingHost(download_callback=self._handle_download)
        self.manifest_paths = self._get_manifest_paths()
        
        # Handle path differently when running as executable
        if getattr(sys, 'frozen', False):
            # If running as compiled executable, use the _MEIPASS directory from PyInstaller
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        else:
            # If running as script, use the script directory
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.extension_dir = os.path.join(base_path, 'browser_extensions')
    
    def start_server(self, port=8765):
        """Start the integration server"""
        self.server.port = port
        return self.server.start()
    
    def stop_server(self):
        """Stop the integration server"""
        self.server.stop()
    
    def is_server_running(self):
        """Check if the server is running"""
        return self.server.is_running()
    
    def _handle_download(self, url, filename=None, referrer=None):
        """Handle download request from browser"""
        if self.download_manager_gui:
            self.download_manager_gui.add_download_from_browser(url, filename, referrer)
    
    def _get_manifest_paths(self):
        """Get paths for browser extension manifests"""
        paths = {}
        
        # Chrome/Edge manifest paths
        if sys.platform == 'win32':
            paths['chrome'] = os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                          'Google', 'Chrome', 'User Data', 'NativeMessagingHosts')
            paths['edge'] = os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                        'Microsoft', 'Edge', 'User Data', 'NativeMessagingHosts')
        elif sys.platform == 'darwin':  # macOS
            paths['chrome'] = os.path.expanduser('~/Library/Application Support/Google/Chrome/NativeMessagingHosts')
            paths['edge'] = os.path.expanduser('~/Library/Application Support/Microsoft Edge/NativeMessagingHosts')
        else:  # Linux
            paths['chrome'] = os.path.expanduser('~/.config/google-chrome/NativeMessagingHosts')
            paths['edge'] = os.path.expanduser('~/.config/microsoft-edge/NativeMessagingHosts')
        
        # Firefox manifest paths
        if sys.platform == 'win32':
            paths['firefox'] = os.path.join(os.environ.get('APPDATA', ''), 
                                           'Mozilla', 'NativeMessagingHosts')
        elif sys.platform == 'darwin':  # macOS
            paths['firefox'] = os.path.expanduser('~/Library/Application Support/Mozilla/NativeMessagingHosts')
        else:  # Linux
            paths['firefox'] = os.path.expanduser('~/.mozilla/native-messaging-hosts')
        
        return paths
    
    def install_chrome_extension(self):
        """Install Chrome extension"""
        # Get source extension directory
        source_ext_dir = os.path.join(self.extension_dir, 'chrome')
        
        # When running as executable, we need to extract the extension files to a user-accessible location
        if getattr(sys, 'frozen', False):
            # Create a directory in the user's appdata folder
            user_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'PyDownloadManager')
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Create extension directory
            chrome_ext_dir = os.path.join(user_data_dir, 'chrome_extension')
            
            # If the extension directory already exists, return it
            if os.path.exists(chrome_ext_dir):
                return chrome_ext_dir
                
            # Otherwise, copy the extension files from the bundled resources
            os.makedirs(chrome_ext_dir, exist_ok=True)
            
            # Copy all files from source to destination
            for root, dirs, files in os.walk(source_ext_dir):
                # Get the relative path from source_ext_dir
                rel_path = os.path.relpath(root, source_ext_dir)
                # Create the corresponding directory in chrome_ext_dir
                if rel_path != '.':
                    os.makedirs(os.path.join(chrome_ext_dir, rel_path), exist_ok=True)
                
                # Copy all files
                for file in files:
                    src_file = os.path.join(root, file)
                    # Get the relative path and join with destination
                    if rel_path == '.':
                        dst_file = os.path.join(chrome_ext_dir, file)
                    else:
                        dst_file = os.path.join(chrome_ext_dir, rel_path, file)
                    
                    # Copy the file
                    with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
                        dst.write(src.read())
        else:
            # When running as script, use the extension directory directly
            chrome_ext_dir = source_ext_dir
            os.makedirs(chrome_ext_dir, exist_ok=True)
            
            # Create icons directory
            icons_dir = os.path.join(chrome_ext_dir, 'icons')
            os.makedirs(icons_dir, exist_ok=True)
            
            # Create placeholder icons if they don't exist
            for size in [16, 48, 128]:
                icon_path = os.path.join(icons_dir, f'icon{size}.png')
                if not os.path.exists(icon_path):
                    with open(icon_path, 'w') as f:
                        f.write(f"Placeholder for {size}x{size} icon")
        
        return chrome_ext_dir
    
    def register_native_messaging_host(self, browser='chrome'):
        """Register native messaging host for browser extension"""
        success = {}
        app_name = 'com.pydownloadmanager.native'
        
        # Get the path to the native messaging host executable or script
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            host_path = sys.executable
        else:
            # Running as script
            host_path = os.path.abspath(sys.argv[0])
            
        # Ensure the path is properly escaped for JSON
        if os.name == 'nt':
            host_path = host_path.replace('\\', '\\\\')
        
        # Create manifest for each browser
        for browser, manifest_dir in self.manifest_paths.items():
            try:
                if not os.path.exists(manifest_dir):
                    os.makedirs(manifest_dir, exist_ok=True)
                
                # Get the extension ID from the manifest.json file if possible
                extension_id = '[extension-id]'  # Default placeholder
                chrome_ext_dir = self.install_chrome_extension()
                manifest_path = os.path.join(chrome_ext_dir, 'manifest.json')
                
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            ext_manifest = json.load(f)
                            # If we have a key in the manifest, use it as the extension ID
                            if 'key' in ext_manifest:
                                # The key would need to be converted to an extension ID
                                # This is a placeholder for that conversion
                                pass
                    except Exception as e:
                        logger.error(f"Error reading extension manifest: {str(e)}")
                
                manifest = {
                    'name': app_name,
                    'description': 'PyDownload Manager Native Messaging Host',
                    'path': host_path,
                    'type': 'stdio',
                    'allowed_origins': [
                        f'chrome-extension://{extension_id}/' if browser in ['chrome', 'edge'] else
                        f'firefox-extension://{extension_id}/'
                    ]
                }
                
                manifest_path = os.path.join(manifest_dir, f'{app_name}.json')
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                success[browser] = True
                logger.info(f"Registered native messaging host for {browser}")
            
            except Exception as e:
                success[browser] = False
                logger.error(f"Failed to register native messaging host for {browser}: {str(e)}")
        
        return success


# Example usage
def main():
    def download_callback(url, filename=None, referrer=None):
        print(f"Download requested: {url}, filename: {filename}, referrer: {referrer}")
    
    integration = BrowserIntegration(download_callback=download_callback)
    integration.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.stop()


if __name__ == "__main__":
    main()