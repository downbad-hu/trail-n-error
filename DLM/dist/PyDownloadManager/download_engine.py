import os
import time
import threading
import queue
import requests
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Callable


class DownloadStatus(Enum):
    QUEUED = 'queued'
    DOWNLOADING = 'downloading'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    ERROR = 'error'
    CANCELED = 'canceled'


@dataclass
class DownloadItem:
    url: str
    save_path: str
    filename: Optional[str] = None
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    total_size: int = 0
    downloaded_size: int = 0
    speed: float = 0.0
    threads: List[threading.Thread] = None
    chunk_info: List[Dict] = None
    start_time: float = 0.0
    error_message: str = ''
    id: str = ''
    referrer: Optional[str] = None
    
    def __post_init__(self):
        if not self.filename:
            self.filename = os.path.basename(urlparse(self.url).path) or 'download'
            if not self.filename or self.filename == '/':
                self.filename = 'download'
        
        if not self.id:
            self.id = str(hash(self.url + self.filename + str(time.time())))
        
        self.threads = []
        self.chunk_info = []


class DownloadEngine:
    def __init__(self, max_concurrent_downloads=3, max_threads_per_download=3, chunk_size=1024*1024):
        self.downloads: Dict[str, DownloadItem] = {}
        self.download_queue = queue.Queue()
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_threads_per_download = max_threads_per_download
        self.chunk_size = chunk_size
        self.active_downloads = 0
        self.queue_lock = threading.Lock()
        self.download_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.queue_processor = threading.Thread(target=self._process_queue)
        self.queue_processor.daemon = True
        self.queue_processor.start()
        self.callbacks = {}
    
    def register_callback(self, event_type, callback):
        """Register callbacks for different events"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def _trigger_callback(self, event_type, download_item):
        """Trigger registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                callback(download_item)
    
    def add_download(self, url, save_path, filename=None, referrer=None) -> str:
        """Add a new download to the queue"""
        download_item = DownloadItem(url=url, save_path=save_path, filename=filename, referrer=referrer)
        
        # Create directory if it doesn't exist
        os.makedirs(download_item.save_path, exist_ok=True)
        
        self.downloads[download_item.id] = download_item
        self.download_queue.put(download_item.id)
        self._trigger_callback('added', download_item)
        return download_item.id
    
    def _process_queue(self):
        """Process the download queue"""
        while not self.stop_event.is_set():
            if self.active_downloads < self.max_concurrent_downloads and not self.download_queue.empty():
                try:
                    download_id = self.download_queue.get(block=False)
                    with self.download_lock:
                        self.active_downloads += 1
                    self._start_download(download_id)
                    self.download_queue.task_done()
                except queue.Empty:
                    pass
            time.sleep(0.5)
    
    def _start_download(self, download_id):
        """Start a download with the given ID"""
        download_item = self.downloads[download_id]
        download_item.status = DownloadStatus.DOWNLOADING
        download_item.start_time = time.time()
        
        # Get file size and check if resume is supported
        try:
            headers = {}
            if download_item.referrer:
                headers['Referer'] = download_item.referrer
                
            response = requests.head(download_item.url, headers=headers, allow_redirects=True)
            total_size = int(response.headers.get('content-length', 0))
            download_item.total_size = total_size
            supports_range = 'accept-ranges' in response.headers and response.headers['accept-ranges'] == 'bytes'
        except Exception as e:
            download_item.status = DownloadStatus.ERROR
            download_item.error_message = str(e)
            with self.download_lock:
                self.active_downloads -= 1
            self._trigger_callback('error', download_item)
            return
        
        # Start download thread
        if supports_range and total_size > 0 and self.max_threads_per_download > 1:
            self._start_multi_threaded_download(download_item)
        else:
            self._start_single_threaded_download(download_item)
        
        self._trigger_callback('started', download_item)
    
    def _start_single_threaded_download(self, download_item):
        """Start a single-threaded download"""
        thread = threading.Thread(
            target=self._download_thread,
            args=(download_item, 0, 0, download_item.total_size)
        )
        thread.daemon = True
        download_item.threads.append(thread)
        thread.start()
    
    def _start_multi_threaded_download(self, download_item):
        """Start a multi-threaded download"""
        total_size = download_item.total_size
        chunk_size = total_size // min(self.max_threads_per_download, total_size // self.chunk_size or 1)
        
        for i in range(min(self.max_threads_per_download, total_size // self.chunk_size or 1)):
            start_byte = i * chunk_size
            end_byte = start_byte + chunk_size - 1 if i < self.max_threads_per_download - 1 else total_size - 1
            
            # Create chunk info
            chunk_info = {
                'start': start_byte,
                'end': end_byte,
                'downloaded': 0,
                'file_path': os.path.join(download_item.save_path, f"{download_item.filename}.part{i}")
            }
            download_item.chunk_info.append(chunk_info)
            
            # Start thread for this chunk
            thread = threading.Thread(
                target=self._download_thread,
                args=(download_item, i, start_byte, end_byte)
            )
            thread.daemon = True
            download_item.threads.append(thread)
            thread.start()
    
    def _download_thread(self, download_item, chunk_index, start_byte, end_byte):
        """Download thread function"""
        try:
            headers = {}
            if start_byte > 0 or end_byte < download_item.total_size - 1:
                headers['Range'] = f'bytes={start_byte}-{end_byte}'
            
            # Add referrer header if available
            if download_item.referrer:
                headers['Referer'] = download_item.referrer
            
            response = requests.get(download_item.url, headers=headers, stream=True)
            
            # Determine file path
            if len(download_item.chunk_info) > 0:
                file_path = download_item.chunk_info[chunk_index]['file_path']
            else:
                file_path = os.path.join(download_item.save_path, download_item.filename)
            
            # Open file for writing
            with open(file_path, 'wb') as f:
                downloaded = 0
                last_update_time = time.time()
                last_downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk and download_item.status != DownloadStatus.PAUSED and download_item.status != DownloadStatus.CANCELED:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update chunk info if multi-threaded
                        if len(download_item.chunk_info) > 0:
                            download_item.chunk_info[chunk_index]['downloaded'] = downloaded
                        
                        # Calculate total progress
                        with self.download_lock:
                            if len(download_item.chunk_info) > 0:
                                total_downloaded = sum(chunk['downloaded'] for chunk in download_item.chunk_info)
                            else:
                                total_downloaded = downloaded
                            
                            download_item.downloaded_size = total_downloaded
                            if download_item.total_size > 0:
                                download_item.progress = total_downloaded / download_item.total_size * 100
                            
                            # Calculate download speed
                            current_time = time.time()
                            if current_time - last_update_time >= 1.0:  # Update speed every second
                                download_item.speed = (total_downloaded - last_downloaded) / (current_time - last_update_time)
                                last_update_time = current_time
                                last_downloaded = total_downloaded
                        
                        # Trigger progress callback
                        self._trigger_callback('progress', download_item)
                    elif download_item.status == DownloadStatus.PAUSED:
                        # Wait while paused
                        while download_item.status == DownloadStatus.PAUSED and not self.stop_event.is_set():
                            time.sleep(0.5)
                    elif download_item.status == DownloadStatus.CANCELED:
                        break
            
            # Check if all threads are done for multi-threaded downloads
            if len(download_item.chunk_info) > 0:
                all_done = True
                for thread in download_item.threads:
                    if thread != threading.current_thread() and thread.is_alive():
                        all_done = False
                        break
                
                if all_done:
                    self._merge_chunks(download_item)
            else:
                # Single-threaded download completed
                download_item.status = DownloadStatus.COMPLETED
                with self.download_lock:
                    self.active_downloads -= 1
                self._trigger_callback('completed', download_item)
        
        except Exception as e:
            download_item.status = DownloadStatus.ERROR
            download_item.error_message = str(e)
            with self.download_lock:
                self.active_downloads -= 1
            self._trigger_callback('error', download_item)
    
    def _merge_chunks(self, download_item):
        """Merge downloaded chunks into a single file"""
        try:
            output_path = os.path.join(download_item.save_path, download_item.filename)
            with open(output_path, 'wb') as output_file:
                for chunk_info in download_item.chunk_info:
                    with open(chunk_info['file_path'], 'rb') as chunk_file:
                        output_file.write(chunk_file.read())
                    # Delete chunk file
                    os.remove(chunk_info['file_path'])
            
            download_item.status = DownloadStatus.COMPLETED
            with self.download_lock:
                self.active_downloads -= 1
            self._trigger_callback('completed', download_item)
        except Exception as e:
            download_item.status = DownloadStatus.ERROR
            download_item.error_message = f"Error merging chunks: {str(e)}"
            with self.download_lock:
                self.active_downloads -= 1
            self._trigger_callback('error', download_item)
    
    def pause_download(self, download_id):
        """Pause a download"""
        if download_id in self.downloads:
            download_item = self.downloads[download_id]
            if download_item.status == DownloadStatus.DOWNLOADING:
                download_item.status = DownloadStatus.PAUSED
                self._trigger_callback('paused', download_item)
                return True
        return False
    
    def resume_download(self, download_id):
        """Resume a paused download"""
        if download_id in self.downloads:
            download_item = self.downloads[download_id]
            if download_item.status == DownloadStatus.PAUSED:
                download_item.status = DownloadStatus.DOWNLOADING
                self._trigger_callback('resumed', download_item)
                return True
        return False
    
    def cancel_download(self, download_id):
        """Cancel a download"""
        if download_id in self.downloads:
            download_item = self.downloads[download_id]
            if download_item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]:
                download_item.status = DownloadStatus.CANCELED
                
                # If download was active, decrease active count
                if download_item.status == DownloadStatus.DOWNLOADING:
                    with self.download_lock:
                        self.active_downloads -= 1
                
                # Clean up partial files
                if len(download_item.chunk_info) > 0:
                    for chunk_info in download_item.chunk_info:
                        if os.path.exists(chunk_info['file_path']):
                            try:
                                os.remove(chunk_info['file_path'])
                            except:
                                pass
                
                self._trigger_callback('canceled', download_item)
                return True
        return False
    
    def get_download_info(self, download_id):
        """Get information about a download"""
        if download_id in self.downloads:
            return self.downloads[download_id]
        return None
    
    def get_all_downloads(self):
        """Get all downloads"""
        return list(self.downloads.values())
    
    def shutdown(self):
        """Shutdown the download engine"""
        self.stop_event.set()
        
        # Cancel all active downloads
        for download_id, download_item in self.downloads.items():
            if download_item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED]:
                self.cancel_download(download_id)
        
        # Wait for queue processor to finish
        if self.queue_processor.is_alive():
            self.queue_processor.join(timeout=2.0)