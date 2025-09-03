// BTC Trading Bot - Dashboard Functions

async function fetchConfig() {
    const statusId = 'config-status';
    showStatus(statusId, 'Fetching configuration...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/config');
        showStatus(statusId, '<strong>Success!</strong><br>' + formatJson(data), 'success');
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function startWebSocket() {
    const statusId = 'ws-status';
    showStatus(statusId, 'Starting WebSocket connection...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/websocket/start', { method: 'POST' });
        showStatus(statusId, '<strong>Success:</strong> ' + data.message, 'success');
        pollWebSocketStatus();
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function stopWebSocket() {
    const statusId = 'ws-status';
    showStatus(statusId, 'Stopping WebSocket connection...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/websocket/stop', { method: 'POST' });
        showStatus(statusId, '<strong>Success:</strong> ' + data.message, 'success');
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function sendTelegramMessage() {
    const messageInput = document.getElementById('telegram-message');
    const message = messageInput.value;
    const statusId = 'telegram-status';
    
    if (!message.trim()) {
        alert('Please enter a message');
        return;
    }
    
    showStatus(statusId, 'Sending Telegram message...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/telegram/send', {
            method: 'POST',
            body: JSON.stringify({ message: message })
        });
        showStatus(statusId, '<strong>Success:</strong> Message sent!', 'success');
        messageInput.value = '';
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function getBitcoinPrice() {
    const statusId = 'bitcoin-status';
    showStatus(statusId, 'Fetching Bitcoin price...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/bitcoin/price');
        showStatus(statusId, '<strong>Bitcoin Price:</strong><br>' + formatJson(data), 'success');
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function getBitcoinCandles() {
    const statusId = 'bitcoin-status';
    showStatus(statusId, 'Fetching Bitcoin candles...', 'loading');
    
    try {
        const data = await apiCall('/api/v1/bitcoin/candles?hours=24');
        showStatus(statusId, '<strong>Bitcoin Candles (24h):</strong><br>' + formatJson(data), 'success');
    } catch (error) {
        showStatus(statusId, '<strong>Error:</strong> ' + error.message, 'error');
    }
}

async function pollWebSocketStatus() {
    try {
        const data = await apiCall('/api/v1/websocket/status');
        const statusId = 'ws-status';
        
        if (data.is_running) {
            const statusContent = '<strong>WebSocket Running</strong><br>Latest Data:<br>' + formatJson(data.latest_data);
            showStatus(statusId, statusContent, 'success');
            setTimeout(pollWebSocketStatus, 3000); // Poll every 3 seconds
        }
    } catch (error) {
        console.log('Polling stopped or error:', error.message);
    }
}