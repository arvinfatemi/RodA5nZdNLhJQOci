"""
Main FastAPI application.
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles  
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.api.api_v1.api import api_router
from app.services.websocket_service import websocket_service

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("FastAPI application starting up")
    yield
    logger.info("FastAPI application shutting down")
    # Clean up WebSocket client if running
    try:
        await websocket_service.stop_websocket()
    except Exception as e:
        logger.warning(f"Error stopping WebSocket during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="FastAPI application for BTC trading bot with Google Sheets config, Coinbase WebSocket, and Telegram notifications",
    version="2.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": settings.app_name}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting {settings.app_name} FastAPI Application...")
    print(f"Visit http://{settings.host}:{settings.port} to access the control panel")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )