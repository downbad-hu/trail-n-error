// PyDownload Manager Chrome Extension - Popup Script

// Default configuration
const defaultConfig = {
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
  minSize: 1 // 1MB minimum file size
};

// Current configuration
let config = { ...defaultConfig };

// DOM elements
const elements = {
  enabled: document.getElementById('enabled'),
  serverUrl: document.getElementById('serverUrl'),
  minSize: document.getElementById('minSize'),
  fileTypes: document.getElementById('fileTypes'),
  saveButton: document.getElementById('save'),
  resetButton: document.getElementById('reset'),
  status: document.getElementById('status')
};

// Initialize popup
function initPopup() {
  // Load current configuration
  chrome.runtime.sendMessage({ action: 'getConfig' }, (response) => {
    if (response) {
      config = response;
      updateUI();
    }
  });
  
  // Check connection to PyDownload Manager
  checkConnection();
  
  // Set up event listeners
  elements.saveButton.addEventListener('click', saveConfig);
  elements.resetButton.addEventListener('click', resetConfig);
}

// Update UI with current configuration
function updateUI() {
  elements.enabled.checked = config.enabled;
  elements.serverUrl.value = config.serverUrl;
  elements.minSize.value = config.minSize;
  
  // Update file types display
  elements.fileTypes.innerHTML = '';
  config.fileTypes.forEach(type => {
    const typeElement = document.createElement('span');
    typeElement.className = 'file-type';
    typeElement.textContent = type;
    elements.fileTypes.appendChild(typeElement);
  });
}

// Save configuration
function saveConfig() {
  // Get values from UI
  config.enabled = elements.enabled.checked;
  config.serverUrl = elements.serverUrl.value;
  config.minSize = parseFloat(elements.minSize.value);
  
  // Send updated configuration to background script
  chrome.runtime.sendMessage({
    action: 'setConfig',
    config: config
  }, (response) => {
    if (response && response.success) {
      showStatus('Settings saved', 'connected');
      setTimeout(() => {
        checkConnection();
      }, 1000);
    } else {
      showStatus('Failed to save settings', 'disconnected');
    }
  });
}

// Reset configuration to defaults
function resetConfig() {
  config = { ...defaultConfig };
  updateUI();
  saveConfig();
}

// Check connection to PyDownload Manager
function checkConnection() {
  showStatus('Checking connection...', '');
  
  fetch(config.serverUrl, {
    method: 'OPTIONS',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      showStatus('Connected to PyDownload Manager', 'connected');
      return true;
    } else {
      throw new Error('Server responded with error');
    }
  })
  .catch(error => {
    showStatus('Not connected to PyDownload Manager', 'disconnected');
    console.error('Connection error:', error);
    return false;
  });
}

// Show status message
function showStatus(message, className) {
  elements.status.textContent = message;
  elements.status.className = 'status ' + className;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initPopup);