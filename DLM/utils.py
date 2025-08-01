import os
import re
import time
from urllib.parse import urlparse


def is_valid_url(url):
    """Check if a URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def format_speed(speed_bytes):
    """Format bytes/second to human-readable speed"""
    return f"{format_size(speed_bytes)}/s"


def format_time(seconds):
    """Format seconds to human-readable time"""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def estimate_time_remaining(downloaded_bytes, total_bytes, speed_bytes):
    """Estimate time remaining for download"""
    if speed_bytes <= 0 or downloaded_bytes >= total_bytes:
        return "--"
    
    remaining_bytes = total_bytes - downloaded_bytes
    seconds_remaining = remaining_bytes / speed_bytes
    
    return format_time(seconds_remaining)


def get_filename_from_url(url):
    """Extract filename from URL"""
    path = urlparse(url).path
    filename = os.path.basename(path)
    
    # If no filename in URL, use a default name
    if not filename or filename == '/':
        return 'download'
    
    return filename


def get_unique_filename(directory, filename):
    """Get a unique filename by appending a number if file exists"""
    base_name, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    
    return new_filename


def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            return False
    return True


def is_downloadable_url(url):
    """Check if URL is likely to be a downloadable file"""
    # List of common file extensions
    file_extensions = [
        '.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.msi', '.dmg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        '.iso', '.apk', '.deb', '.rpm'
    ]
    
    # Check if URL ends with a common file extension
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in file_extensions)