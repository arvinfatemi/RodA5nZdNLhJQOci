// BTC Trading Bot - Main JavaScript

// Utility functions
function showStatus(elementId, message, type = 'loading') {
    const element = document.getElementById(elementId);
    element.style.display = 'block';
    element.className = `status ${type}`;
    element.innerHTML = message;
}

function hideStatus(elementId) {
    const element = document.getElementById(elementId);
    element.style.display = 'none';
}

// API utility function
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        throw new Error(`API call failed: ${error.message}`);
    }
}

// Format JSON for display
function formatJson(obj) {
    return '<pre>' + JSON.stringify(obj, null, 2) + '</pre>';
}