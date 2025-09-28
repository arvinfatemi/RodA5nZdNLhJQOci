#!/usr/bin/env python3
"""
BTC Trading Bot FastAPI Application Launcher

This script provides a simple menu system to start the FastAPI application
or run individual components as before.
"""

import sys
import subprocess
import os

def print_menu():
    print("=" * 60)
    print("          BTC Trading Bot Control Panel")
    print("=" * 60)
    print()
    print("Choose an option:")
    print()
    print("1. Start FastAPI Web Application (Recommended)")
    print("   - Web interface with all 3 functionalities")
    print("   - Access at http://localhost:8000")
    print()
    print("2. Fetch Google Sheets Configuration (Legacy)")
    print("   - Command line config fetch only")
    print()
    print("3. Start Coinbase WebSocket (Legacy)")
    print("   - Command line WebSocket connection only")
    print()
    print("4. Send Telegram Message (Legacy)")
    print("   - Command line Telegram message only")
    print()
    print("5. Get Bitcoin Prices & Candles (Legacy)")
    print("   - Command line Bitcoin price and candle data fetch")
    print()
    print("6. Exit")
    print()

def run_fastapi():
    """Start the FastAPI application"""
    print("Starting FastAPI application...")
    print("Visit http://localhost:8000 to access the web interface")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Run the FastAPI application
        subprocess.run([sys.executable, "-m", "app.main"], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running FastAPI application: {e}")
    except FileNotFoundError:
        print("Error: app module not found. Make sure you're in the correct directory.")

def run_config_fetch():
    """Run Google Sheets config fetch"""
    print("Fetching configuration from Google Sheets...")
    print("-" * 60)
    
    try:
        import asyncio
        import json
        from app.services.config_service import ConfigService

        async def fetch_config():
            config_service = ConfigService()
            config = await config_service.get_config()
            return config

        config = asyncio.run(fetch_config())

        print("Configuration loaded successfully:")
        print(json.dumps(config.dict() if hasattr(config, 'dict') else config, indent=2))
        
    except Exception as e:
        print(f"Error fetching configuration: {e}")

def run_websocket():
    """Run Coinbase WebSocket connection"""
    print("Starting Coinbase WebSocket connection...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # WebSocket functionality is now integrated into the FastAPI app
        print("WebSocket functionality is now integrated into the FastAPI application.")
        print("Use option 1 to start the full application with WebSocket support.")
    except KeyboardInterrupt:
        print("\nWebSocket stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running WebSocket: {e}")
    except FileNotFoundError:
        print("WebSocket is now integrated into the main application.")

def run_telegram():
    """Send a Telegram message"""
    print("Send Telegram Message")
    print("-" * 60)
    
    message = input("Enter your message: ").strip()
    if not message:
        print("No message entered.")
        return
    
    try:
        import asyncio
        from app.services.telegram_service import TelegramService

        async def send_message():
            telegram_service = TelegramService()
            result = await telegram_service.send_message(text=message)
            return result

        result = asyncio.run(send_message())

        print("Message sent successfully!")
        print(f"Response: {result}")

    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def run_bitcoin_data():
    """Fetch Bitcoin price and candles data"""
    print("Bitcoin Price & Candles Data")
    print("-" * 60)
    
    try:
        # Try to import Coinbase SDK
        try:
            from coinbase.rest import RESTClient
        except ImportError:
            print("Error: Coinbase Advanced Python SDK not available.")
            print("Install with: pip install coinbase-advanced-py")
            return
        
        # Initialize client
        client = RESTClient()
        
        print("1. Current Bitcoin Price")
        print("2. Bitcoin Candles (Last 24 hours)")
        print("3. Both")
        choice = input("Choose option (1-3): ").strip()
        
        if choice in ["1", "3"]:
            print("\nFetching current Bitcoin price...")
            try:
                # Try authenticated SDK first, fallback to public API
                try:
                    ticker = client.get_product_ticker("BTC-USD")
                    product = client.get_product("BTC-USD")
                    
                    print("\n" + "="*50)
                    print("BITCOIN PRICE DATA (Authenticated)")
                    print("="*50)
                    print(f"Current Price: ${float(ticker.price):,.2f}")
                    if ticker.price_percentage_change_24h:
                        change = float(ticker.price_percentage_change_24h)
                        print(f"24h Change: {change:+.2f}%")
                    if ticker.volume_24h:
                        print(f"24h Volume: ${float(ticker.volume_24h):,.2f}")
                    if ticker.best_bid and ticker.best_ask:
                        print(f"Bid/Ask: ${float(ticker.best_bid):,.2f} / ${float(ticker.best_ask):,.2f}")
                    print(f"Product Status: {getattr(product, 'status', 'Unknown')}")
                    print("="*50)
                    
                except Exception as auth_error:
                    print(f"Authenticated API failed, using public API: {auth_error}")
                    
                    # Use public API fallback
                    import requests
                    
                    # Get ticker and stats from public API
                    ticker_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker")
                    ticker_response.raise_for_status()
                    ticker_data = ticker_response.json()
                    
                    stats_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/stats")
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    
                    print("\n" + "="*50)
                    print("BITCOIN PRICE DATA (Public API)")
                    print("="*50)
                    print(f"Current Price: ${float(ticker_data['price']):,.2f}")
                    
                    # Calculate 24h change if we have open price
                    if stats_data.get('open'):
                        current_price = float(ticker_data['price'])
                        open_price = float(stats_data['open'])
                        change_pct = ((current_price - open_price) / open_price) * 100
                        print(f"24h Change: {change_pct:+.2f}%")
                    
                    print(f"24h High: ${float(stats_data.get('high', 0)):,.2f}")
                    print(f"24h Low: ${float(stats_data.get('low', 0)):,.2f}")
                    print(f"24h Volume: ${float(ticker_data.get('volume', 0)):,.2f}")
                    
                    if ticker_data.get('bid') and ticker_data.get('ask'):
                        print(f"Bid/Ask: ${float(ticker_data['bid']):,.2f} / ${float(ticker_data['ask']):,.2f}")
                    
                    print("="*50)
                
            except Exception as e:
                print(f"Error fetching price data: {e}")
        
        if choice in ["2", "3"]:
            print("\nFetching Bitcoin candles (last 24 hours)...")
            try:
                from datetime import datetime, timedelta
                import requests
                
                # Calculate time range
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                try:
                    # Try authenticated SDK first
                    candles = client.get_candles(
                        product_id="BTC-USD",
                        start=start_time.isoformat(),
                        end=end_time.isoformat(),
                        granularity="ONE_HOUR"
                    )
                    
                    print("\n" + "="*80)
                    print("BITCOIN CANDLES (HOURLY - LAST 24 HOURS) - Authenticated")
                    print("="*80)
                    print(f"{'Timestamp':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
                    print("-"*80)
                    
                    # Convert and sort candles
                    candle_data = []
                    for candle in candles:
                        candle_data.append({
                            'timestamp': candle.start,
                            'open': float(candle.open),
                            'high': float(candle.high),
                            'low': float(candle.low),
                            'close': float(candle.close),
                            'volume': float(candle.volume)
                        })
                    
                    # Sort by timestamp (most recent first) and show last 10
                    candle_data.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    for i, candle in enumerate(candle_data[:10]):  # Show last 10 candles
                        ts = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
                        ts_str = ts.strftime('%m-%d %H:%M')
                        print(f"{ts_str:<20} ${candle['open']:<9.2f} ${candle['high']:<9.2f} ${candle['low']:<9.2f} ${candle['close']:<9.2f} {candle['volume']:<12.2f}")
                    
                    if len(candle_data) > 10:
                        print(f"\n... and {len(candle_data)-10} more candles")
                    
                    print("="*80)
                    
                except Exception as auth_error:
                    print(f"Authenticated API failed, using public API: {auth_error}")
                    
                    # Use public API fallback
                    params = {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "granularity": 3600  # 1 hour in seconds
                    }
                    
                    candles_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/candles", params=params)
                    candles_response.raise_for_status()
                    candles_raw = candles_response.json()
                    
                    print("\n" + "="*80)
                    print("BITCOIN CANDLES (HOURLY - LAST 24 HOURS) - Public API")
                    print("="*80)
                    print(f"{'Timestamp':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
                    print("-"*80)
                    
                    # Convert to our format (public API returns [timestamp, low, high, open, close, volume])
                    candle_data = []
                    for candle in candles_raw:
                        if len(candle) >= 6:
                            candle_data.append({
                                'timestamp': datetime.fromtimestamp(candle[0]).isoformat() + "Z",
                                'open': float(candle[3]),  # Open is at index 3
                                'high': float(candle[2]),  # High is at index 2
                                'low': float(candle[1]),   # Low is at index 1
                                'close': float(candle[4]), # Close is at index 4
                                'volume': float(candle[5]) # Volume is at index 5
                            })
                    
                    # Sort by timestamp (most recent first) and show last 10
                    candle_data.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    for i, candle in enumerate(candle_data[:10]):  # Show last 10 candles
                        ts = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
                        ts_str = ts.strftime('%m-%d %H:%M')
                        print(f"{ts_str:<20} ${candle['open']:<9.2f} ${candle['high']:<9.2f} ${candle['low']:<9.2f} ${candle['close']:<9.2f} {candle['volume']:<12.2f}")
                    
                    if len(candle_data) > 10:
                        print(f"\n... and {len(candle_data)-10} more candles")
                    
                    print("="*80)
                
            except Exception as e:
                print(f"Error fetching candle data: {e}")
        
    except Exception as e:
        print(f"Error in Bitcoin data fetch: {e}")

def main():
    """Main menu loop"""
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == "1":
                run_fastapi()
            elif choice == "2":
                run_config_fetch()
            elif choice == "3":
                run_websocket()
            elif choice == "4":
                run_telegram()
            elif choice == "5":
                run_bitcoin_data()
            elif choice == "6":
                print("Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")
            
            # Wait for user before showing menu again
            input("\nPress Enter to continue...")
            print("\n" * 2)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\nGoodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()