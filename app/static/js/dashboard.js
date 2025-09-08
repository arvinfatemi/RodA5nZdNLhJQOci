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

async function checkPurchaseDecision() {
    const statusId = 'decision-status';
    showStatus(statusId, 'Analyzing market conditions...', 'loading');
    
    try {
        // Step 1: Get trading decision
        showStatus(statusId, '1/3 Getting trading decision...', 'loading');
        const decisionData = await apiCall('/api/v1/trading/decision');
        
        const decision = decisionData.decision;
        const config = decisionData.config;
        const history = decisionData.purchase_history_summary;
        
        // Step 2: Get current Bitcoin price for display
        showStatus(statusId, '2/3 Fetching current Bitcoin price...', 'loading');
        const priceData = await apiCall('/api/v1/bitcoin/price');
        const currentPrice = priceData.data.current_price;
        
        // Step 3: Send decision to Telegram
        showStatus(statusId, '3/3 Sending decision to Telegram...', 'loading');
        
        const telegramMessage = formatDecisionMessage(decision, config, history, currentPrice);
        await apiCall('/api/v1/telegram/send', {
            method: 'POST',
            body: JSON.stringify({ message: telegramMessage })
        });
        
        // Show final result
        const resultHtml = `
            <div class="decision-result">
                <strong>✅ Decision Analysis Complete!</strong><br><br>
                <div class="decision-summary ${decision.should_buy ? 'buy-decision' : 'wait-decision'}">
                    <strong>${decision.should_buy ? '🟢 BUY' : '🔴 WAIT'}</strong><br>
                    ${decision.reason}
                </div>
                <br>
                <strong>Current Price:</strong> $${currentPrice?.toLocaleString()}<br>
                <strong>Config:</strong> $${config.purchase_amount_usd} at ${config.drop_percentage_threshold}% drop<br>
                <strong>Last Purchase:</strong> $${decision.last_purchase_price?.toLocaleString() || 'None'}<br>
                ${decision.price_drop_percentage ? `<strong>Price Change:</strong> ${decision.price_drop_percentage.toFixed(2)}%<br>` : ''}
                <br>
                <em>📱 Decision sent to Telegram!</em>
            </div>
        `;
        
        showStatus(statusId, resultHtml, 'success');
        
    } catch (error) {
        showStatus(statusId, '<strong>❌ Error:</strong> ' + error.message, 'error');
    }
}

function formatDecisionMessage(decision, config, history, currentPrice) {
    const emoji = decision.should_buy ? '🟢' : '🔴';
    const action = decision.should_buy ? 'BUY' : 'WAIT';
    
    let message = `🧠 **Bitcoin Trading Decision**\n\n`;
    message += `${emoji} **${action}**\n`;
    message += `${decision.reason}\n\n`;
    
    message += `💰 **Current Price:** $${currentPrice?.toLocaleString()}\n`;
    message += `📊 **Config:** $${config.purchase_amount_usd} at ${config.drop_percentage_threshold}% drop\n`;
    
    if (decision.last_purchase_price) {
        message += `📈 **Last Purchase:** $${decision.last_purchase_price.toLocaleString()}\n`;
    }
    
    if (decision.price_drop_percentage) {
        const changeEmoji = decision.price_drop_percentage > 0 ? '📉' : '📈';
        message += `${changeEmoji} **Price Change:** ${decision.price_drop_percentage.toFixed(2)}%\n`;
    }
    
    if (decision.should_buy && decision.recommended_amount_usd) {
        message += `\n💵 **Recommended Purchase:** $${decision.recommended_amount_usd}\n`;
    }
    
    message += `\n📊 **Portfolio Summary:**\n`;
    message += `• Total Purchases: ${history.total_purchases}\n`;
    message += `• Total Invested: $${history.total_invested_usd?.toLocaleString()}\n`;
    message += `• Avg Price: $${history.average_price?.toLocaleString()}\n`;
    
    message += `\n⏰ ${new Date().toLocaleString()}`;
    
    return message;
}