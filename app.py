import asyncio
import json
import logging
import threading
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

from config_loader import read_app_config_from_sheet
from ws_client import connect_coinbase_ws, CoinbaseWSClient
from telegram_notifier import send_telegram_message, resolve_and_cache_chat_id


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ws_client_instance: Optional[CoinbaseWSClient] = None
ws_data_storage = {
    "ticker": None,
    "candle": None,
    "heartbeat": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI application starting up")
    yield
    logger.info("FastAPI application shutting down")
    if ws_client_instance:
        logger.info("Stopping WebSocket client")
        ws_client_instance.stop()

app = FastAPI(
    title="BTC Trading Bot API",
    description="FastAPI application for BTC trading bot with Google Sheets config, Coinbase WebSocket, and Telegram notifications",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BTC Trading Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .option { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .option h3 { color: #333; margin-top: 0; }
            .option p { color: #666; }
            button { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 3px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .status { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>BTC Trading Bot Control Panel</h1>
        <p>Choose from the available options:</p>
        
        <div class="option">
            <h3>1. Fetch Configuration from Google Sheets</h3>
            <p>Load trading bot configuration from your Google Sheets document.</p>
            <button onclick="fetchConfig()">Fetch Config</button>
            <div id="config-status" class="status" style="display:none;"></div>
        </div>
        
        <div class="option">
            <h3>2. Start Coinbase WebSocket Connection</h3>
            <p>Connect to Coinbase WebSocket for real-time BTC price data and candles.</p>
            <button onclick="startWebSocket()">Start WebSocket</button>
            <button onclick="stopWebSocket()">Stop WebSocket</button>
            <div id="ws-status" class="status" style="display:none;"></div>
        </div>
        
        <div class="option">
            <h3>3. Send Telegram Message</h3>
            <p>Send a test message via Telegram bot.</p>
            <input type="text" id="telegram-message" placeholder="Enter your message" style="width: 300px; margin-right: 10px;">
            <button onclick="sendTelegramMessage()">Send Message</button>
            <div id="telegram-status" class="status" style="display:none;"></div>
        </div>

        <script>
            async function fetchConfig() {
                const status = document.getElementById('config-status');
                status.style.display = 'block';
                status.textContent = 'Fetching configuration...';
                
                try {
                    const response = await fetch('/config');
                    const data = await response.json();
                    if (response.ok) {
                        status.innerHTML = '<strong>Success!</strong><br><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        status.innerHTML = '<strong>Error:</strong> ' + data.detail;
                    }
                } catch (error) {
                    status.innerHTML = '<strong>Error:</strong> ' + error.message;
                }
            }

            async function startWebSocket() {
                const status = document.getElementById('ws-status');
                status.style.display = 'block';
                status.textContent = 'Starting WebSocket connection...';
                
                try {
                    const response = await fetch('/websocket/start', { method: 'POST' });
                    const data = await response.json();
                    if (response.ok) {
                        status.innerHTML = '<strong>Success:</strong> ' + data.message;
                        pollWebSocketStatus();
                    } else {
                        status.innerHTML = '<strong>Error:</strong> ' + data.detail;
                    }
                } catch (error) {
                    status.innerHTML = '<strong>Error:</strong> ' + error.message;
                }
            }

            async function stopWebSocket() {
                const status = document.getElementById('ws-status');
                status.style.display = 'block';
                status.textContent = 'Stopping WebSocket connection...';
                
                try {
                    const response = await fetch('/websocket/stop', { method: 'POST' });
                    const data = await response.json();
                    if (response.ok) {
                        status.innerHTML = '<strong>Success:</strong> ' + data.message;
                    } else {
                        status.innerHTML = '<strong>Error:</strong> ' + data.detail;
                    }
                } catch (error) {
                    status.innerHTML = '<strong>Error:</strong> ' + error.message;
                }
            }

            async function sendTelegramMessage() {
                const messageInput = document.getElementById('telegram-message');
                const message = messageInput.value;
                const status = document.getElementById('telegram-status');
                
                if (!message.trim()) {
                    alert('Please enter a message');
                    return;
                }
                
                status.style.display = 'block';
                status.textContent = 'Sending Telegram message...';
                
                try {
                    const response = await fetch('/telegram/send', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        status.innerHTML = '<strong>Success:</strong> Message sent!';
                        messageInput.value = '';
                    } else {
                        status.innerHTML = '<strong>Error:</strong> ' + data.detail;
                    }
                } catch (error) {
                    status.innerHTML = '<strong>Error:</strong> ' + error.message;
                }
            }

            async function pollWebSocketStatus() {
                try {
                    const response = await fetch('/websocket/status');
                    const data = await response.json();
                    const status = document.getElementById('ws-status');
                    
                    if (data.is_running) {
                        status.innerHTML = '<strong>WebSocket Running</strong><br>Latest Data:<br><pre>' + 
                            JSON.stringify(data.latest_data, null, 2) + '</pre>';
                        setTimeout(pollWebSocketStatus, 3000); // Poll every 3 seconds
                    }
                } catch (error) {
                    console.log('Polling stopped or error:', error.message);
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/config")
async def get_config():
    """Fetch configuration from Google Sheets"""
    try:
        sheet_id = '1A58QwxlFcy2zJGfcPRlBLtlaoC7eundbS6DpG24nMao'
        worksheet_name = 'Sheet1'
        cache_path = "./config_cache.json"
        
        config = read_app_config_from_sheet(
            sheet_id=sheet_id,
            worksheet_name=worksheet_name,
            cache_path=cache_path,
            use_cache_if_recent=True,
        )
        
        return {"success": True, "config": config}
    except Exception as e:
        logger.error(f"Failed to fetch config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch configuration: {str(e)}")

@app.post("/websocket/start")
async def start_websocket():
    """Start Coinbase WebSocket connection"""
    global ws_client_instance
    
    if ws_client_instance and hasattr(ws_client_instance, '_thread') and ws_client_instance._thread and ws_client_instance._thread.is_alive():
        return {"success": True, "message": "WebSocket is already running"}
    
    try:
        def on_ticker(msg: dict):
            ws_data_storage["ticker"] = msg
            logger.info(f"Received ticker: {json.dumps(msg, separators=(',', ':'))}")

        def on_candle(msg: dict):
            ws_data_storage["candle"] = msg
            logger.info(f"Received candle: {json.dumps(msg, separators=(',', ':'))}")

        def on_heartbeat(msg: dict):
            ws_data_storage["heartbeat"] = msg
            logger.info(f"Received heartbeat: {json.dumps({k: msg.get(k) for k in ('channel', 'product_id', 'time', 'sequence')}, separators=(',', ':'))}")

        ws_client_instance = connect_coinbase_ws(
            products=["BTC-USD"],
            granularity="30m",
            on_ticker=on_ticker,
            on_candle=on_candle,
            on_heartbeat=on_heartbeat,
            use_sdk_preferred=False,
        )
        
        return {"success": True, "message": "WebSocket connection started successfully"}
    except Exception as e:
        logger.error(f"Failed to start WebSocket: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start WebSocket: {str(e)}")

@app.post("/websocket/stop")
async def stop_websocket():
    """Stop Coinbase WebSocket connection"""
    global ws_client_instance
    
    if not ws_client_instance:
        return {"success": True, "message": "WebSocket is not running"}
    
    try:
        ws_client_instance.stop()
        ws_client_instance = None
        
        # Clear stored data
        for key in ws_data_storage:
            ws_data_storage[key] = None
            
        return {"success": True, "message": "WebSocket connection stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop WebSocket: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop WebSocket: {str(e)}")

@app.get("/websocket/status")
async def get_websocket_status():
    """Get WebSocket connection status and latest data"""
    global ws_client_instance
    
    is_running = (
        ws_client_instance is not None 
        and hasattr(ws_client_instance, '_thread') 
        and ws_client_instance._thread is not None 
        and ws_client_instance._thread.is_alive()
    )
    
    return {
        "is_running": is_running,
        "latest_data": ws_data_storage
    }

@app.post("/telegram/send")
async def send_telegram(request: Dict[str, Any]):
    """Send a message via Telegram"""
    try:
        message = request.get("message")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Try to resolve and cache chat ID if not already available
        try:
            chat_id = resolve_and_cache_chat_id()
        except Exception as e:
            logger.warning(f"Could not resolve chat ID automatically: {e}")
            chat_id = None
        
        result = send_telegram_message(
            text=message,
            chat_id=str(chat_id) if chat_id else None,
        )
        
        return {"success": True, "message": "Telegram message sent successfully", "result": result}
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send Telegram message: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    print("Starting BTC Trading Bot FastAPI Application...")
    print("Visit http://localhost:8000 to access the control panel")
    uvicorn.run(app, host="0.0.0.0", port=8000)