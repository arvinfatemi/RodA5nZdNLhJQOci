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
    print("5. Exit")
    print()

def run_fastapi():
    """Start the FastAPI application"""
    print("Starting FastAPI application...")
    print("Visit http://localhost:8000 to access the web interface")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Run the FastAPI application
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running FastAPI application: {e}")
    except FileNotFoundError:
        print("Error: app.py not found. Make sure you're in the correct directory.")

def run_config_fetch():
    """Run Google Sheets config fetch"""
    print("Fetching configuration from Google Sheets...")
    print("-" * 60)
    
    try:
        # Import and run config loader
        from config_loader import read_app_config_from_sheet
        import json
        
        sheet_id = '1A58QwxlFcy2zJGfcPRlBLtlaoC7eundbS6DpG24nMao'
        worksheet_name = 'Sheet1'
        cache_path = "./config_cache.json"
        
        config = read_app_config_from_sheet(
            sheet_id=sheet_id,
            worksheet_name=worksheet_name,
            cache_path=cache_path,
            use_cache_if_recent=True,
        )
        
        print("Configuration loaded successfully:")
        print(json.dumps(config, indent=2))
        
    except Exception as e:
        print(f"Error fetching configuration: {e}")

def run_websocket():
    """Run Coinbase WebSocket connection"""
    print("Starting Coinbase WebSocket connection...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Run the original main.py with WebSocket only
        subprocess.run([sys.executable, "main.py", "--ws-only"], check=True)
    except KeyboardInterrupt:
        print("\nWebSocket stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running WebSocket: {e}")
    except FileNotFoundError:
        print("Error: main.py not found. Make sure you're in the correct directory.")

def run_telegram():
    """Send a Telegram message"""
    print("Send Telegram Message")
    print("-" * 60)
    
    message = input("Enter your message: ").strip()
    if not message:
        print("No message entered.")
        return
    
    try:
        from telegram_notifier import send_telegram_message, resolve_and_cache_chat_id
        
        # Try to resolve chat ID
        try:
            chat_id = resolve_and_cache_chat_id()
            print(f"Using chat ID: {chat_id}")
        except Exception as e:
            print(f"Could not auto-resolve chat ID: {e}")
            chat_id = None
        
        # Send message
        result = send_telegram_message(
            text=message,
            chat_id=str(chat_id) if chat_id else None,
        )
        
        print("Message sent successfully!")
        print(f"Response: {result}")
        
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def main():
    """Main menu loop"""
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                run_fastapi()
            elif choice == "2":
                run_config_fetch()
            elif choice == "3":
                run_websocket()
            elif choice == "4":
                run_telegram()
            elif choice == "5":
                print("Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
            
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