// PyDownload Manager Chrome Extension - Content Script

// Configuration (will be updated from background script)
let config = {
  enabled: true
};

// Initialize content script
function init() {
  // Get configuration from background script
  chrome.runtime.sendMessage({ action: 'getConfig' }, (response) => {
    if (response) {
      config = response;
    }
  });
  
  // Add download buttons to media elements
  addDownloadButtons();
  
  // Monitor DOM changes to add download buttons to new elements
  observeDOMChanges();
}

// Add download buttons to media elements
function addDownloadButtons() {
  // Find video and audio elements
  const mediaElements = document.querySelectorAll('video[src], audio[src]');
  
  mediaElements.forEach(element => {
    // Skip if already processed
    if (element.dataset.pdmProcessed) return;
    element.dataset.pdmProcessed = 'true';
    
    // Create download button
    const button = document.createElement('button');
    button.className = 'pdm-download-button';
    button.textContent = 'Download with PDM';
    button.style.cssText = 'position: absolute; z-index: 9999; background: rgba(0, 0, 0, 0.7); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;';
    button.style.display = 'none';
    
    // Position the button
    const container = element.parentElement;
    container.style.position = 'relative';
    container.appendChild(button);
    
    // Show button on hover
    element.addEventListener('mouseover', () => {
      if (config.enabled) {
        button.style.display = 'block';
        button.style.top = '10px';
        button.style.right = '10px';
      }
    });
    
    container.addEventListener('mouseleave', () => {
      button.style.display = 'none';
    });
    
    // Handle click
    button.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const url = element.src;
      const filename = getFilenameFromUrl(url);
      
      chrome.runtime.sendMessage({
        action: 'downloadUrl',
        url: url,
        filename: filename
      });
    });
  });
}

// Observe DOM changes to add download buttons to new elements
function observeDOMChanges() {
  const observer = new MutationObserver((mutations) => {
    let shouldAddButtons = false;
    
    mutations.forEach(mutation => {
      if (mutation.addedNodes.length) {
        shouldAddButtons = true;
      }
    });
    
    if (shouldAddButtons) {
      addDownloadButtons();
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Get all downloadable links on the page
function getAllLinks() {
  const links = [];
  const elements = document.querySelectorAll('a[href]');
  
  elements.forEach(element => {
    const url = element.href;
    if (isDownloadableUrl(url)) {
      links.push({
        url: url,
        filename: getFilenameFromUrl(url),
        text: element.textContent.trim()
      });
    }
  });
  
  return links;
}

// Check if URL is likely to be a downloadable file
function isDownloadableUrl(url) {
  if (!url) return false;
  
  // Check if URL has a file extension that matches our config
  const extension = getFileExtension(url);
  return extension && config.fileTypes.includes(extension.toLowerCase());
}

// Get file extension from URL
function getFileExtension(url) {
  try {
    const pathname = new URL(url).pathname;
    const match = pathname.match(/\.([^.\\/:*?"<>|]+)$/i);
    return match ? '.' + match[1].toLowerCase() : null;
  } catch (e) {
    return null;
  }
}

// Get filename from URL
function getFilenameFromUrl(url) {
  try {
    const pathname = new URL(url).pathname;
    const filename = pathname.split('/').pop();
    return filename || 'download';
  } catch (e) {
    return 'download';
  }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getAllLinks') {
    const links = getAllLinks();
    chrome.runtime.sendMessage({
      action: 'downloadLinks',
      links: links
    });
    sendResponse({ success: true, count: links.length });
  }
  
  return true; // Keep the message channel open for async response
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}