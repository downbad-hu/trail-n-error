// PyDownload Manager Chrome Extension - Background Script

// Configuration
const config = {
  enabled: true,
  serverUrl: 'http://127.0.0.1:8765',
  fileTypes: [
    // Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
    // Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    // Media
    '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    // Executables
    '.exe', '.msi', '.dmg', '.iso', '.apk', '.deb', '.rpm'
  ],
  minSize: 1024 * 1024 // 1MB minimum file size
};

// Initialize extension
function initExtension() {
  // Load saved configuration
  chrome.storage.sync.get(['enabled', 'serverUrl', 'fileTypes', 'minSize'], (result) => {
    if (result.enabled !== undefined) config.enabled = result.enabled;
    if (result.serverUrl) config.serverUrl = result.serverUrl;
    if (result.fileTypes) config.fileTypes = result.fileTypes;
    if (result.minSize) config.minSize = result.minSize;
    
    // Update extension icon based on enabled state
    updateIcon();
  });
  
  // Create context menu items
  createContextMenus();
  
  // Connect to native messaging host
  connectToNativeHost();
}

// Update extension icon based on enabled state
function updateIcon() {
  const iconPath = config.enabled ? 'icons/icon48.png' : 'icons/icon48_disabled.png';
  chrome.action.setIcon({ path: iconPath });
}

// Create context menu items
function createContextMenus() {
  chrome.contextMenus.create({
    id: 'downloadWithPDM',
    title: 'Download with PyDownload Manager',
    contexts: ['link']
  });
  
  chrome.contextMenus.create({
    id: 'downloadAllLinks',
    title: 'Download All Links',
    contexts: ['page']
  });
}

// Connect to native messaging host
function connectToNativeHost() {
  try {
    const port = chrome.runtime.connectNative('com.pydownloadmanager.native');
    
    port.onMessage.addListener((message) => {
      console.log('Received message from native host:', message);
    });
    
    port.onDisconnect.addListener(() => {
      console.log('Disconnected from native host:', chrome.runtime.lastError);
    });
    
    // Store port for later use
    window.nativePort = port;
  } catch (error) {
    console.error('Failed to connect to native host:', error);
  }
}

// Send download to PyDownload Manager
function sendDownloadToPDM(url, filename, referrer) {
  // Try native messaging first
  if (window.nativePort) {
    try {
      window.nativePort.postMessage({ url, filename, referrer });
      return true;
    } catch (error) {
      console.error('Native messaging failed:', error);
    }
  }
  
  // Fall back to HTTP API
  return fetch(config.serverUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url, filename, referrer })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Download sent to PyDownload Manager:', data);
    return data.status === 'success';
  })
  .catch(error => {
    console.error('Failed to send download to PyDownload Manager:', error);
    return false;
  });
}

// Intercept downloads
chrome.downloads.onCreated.addListener((downloadItem) => {
  if (!config.enabled) return;
  
  // Check if this download should be handled by PyDownload Manager
  const url = downloadItem.url;
  const filename = downloadItem.filename;
  const fileSize = downloadItem.fileSize || 0;
  
  // Skip small files
  if (fileSize > 0 && fileSize < config.minSize) return;
  
  // Check file extension
  const fileExtension = getFileExtension(filename);
  if (!fileExtension || !config.fileTypes.includes(fileExtension.toLowerCase())) return;
  
  // Cancel Chrome's download
  chrome.downloads.cancel(downloadItem.id, () => {
    // Send to PyDownload Manager
    sendDownloadToPDM(url, filename, downloadItem.referrer);
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!config.enabled) return;
  
  if (info.menuItemId === 'downloadWithPDM' && info.linkUrl) {
    // Download single link
    sendDownloadToPDM(info.linkUrl, null, tab.url);
  } else if (info.menuItemId === 'downloadAllLinks') {
    // Send message to content script to get all links
    chrome.tabs.sendMessage(tab.id, { action: 'getAllLinks' });
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'downloadUrl') {
    // Download URL from content script
    sendDownloadToPDM(message.url, message.filename, sender.tab.url);
    sendResponse({ success: true });
  } else if (message.action === 'downloadLinks') {
    // Download multiple links from content script
    message.links.forEach(link => {
      sendDownloadToPDM(link.url, link.filename, sender.tab.url);
    });
    sendResponse({ success: true, count: message.links.length });
  } else if (message.action === 'getConfig') {
    // Return current configuration
    sendResponse(config);
  } else if (message.action === 'setConfig') {
    // Update configuration
    Object.assign(config, message.config);
    chrome.storage.sync.set(message.config);
    updateIcon();
    sendResponse({ success: true });
  }
  
  return true; // Keep the message channel open for async response
});

// Helper function to get file extension
function getFileExtension(filename) {
  if (!filename) return null;
  const match = filename.match(/\.([^.\\/:*?"<>|]+)$/i);
  return match ? '.' + match[1].toLowerCase() : null;
}

// Initialize extension when loaded
initExtension();