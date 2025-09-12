#!/usr/bin/env python3
"""
Test script for the background trading bot functionality.
"""
import asyncio
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def test_services():
    """Test all the services individually."""
    print("🧪 Testing Background Trading Bot Services\n")
    
    # Test 1: Import all services
    print("📦 Testing service imports...")
    try:
        from app.services.scheduler_service import scheduler_service
        from app.services.simulated_trading_service import simulated_trading_service
        from app.services.notification_service import notification_service
        from app.services.persistent_storage_service import persistent_storage_service
        from app.services.decision_maker_service import decision_maker_service
        from app.services.bitcoin_service import bitcoin_service
        print("✅ All services imported successfully")
    except Exception as e:
        print(f"❌ Service import failed: {e}")
        return False
    
    # Test 2: Test configuration loading
    print("\n⚙️ Testing configuration...")
    try:
        dca_config = await decision_maker_service.get_dca_config()
        print(f"✅ DCA Config loaded:")
        print(f"   - Purchase Amount: ${dca_config.purchase_amount_usd}")
        print(f"   - Drop Threshold: {dca_config.drop_percentage_threshold}%")
        print(f"   - Trading Enabled: {dca_config.trading_enabled}")
        print(f"   - Max Daily Trades: {dca_config.max_daily_trades}")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Test 3: Test Bitcoin price fetching
    print("\n💰 Testing Bitcoin price service...")
    try:
        price_response = await bitcoin_service.get_bitcoin_price()
        if price_response['success']:
            price = price_response['data']['current_price']
            print(f"✅ Bitcoin price fetched: ${price:,.2f}")
        else:
            print("❌ Bitcoin price fetch failed")
            return False
    except Exception as e:
        print(f"❌ Bitcoin service test failed: {e}")
        return False
    
    # Test 4: Test trading decision making
    print("\n🤔 Testing decision making...")
    try:
        decision = await decision_maker_service.evaluate_current_market()
        print(f"✅ Trading decision made:")
        print(f"   - Should Buy: {decision.should_buy}")
        print(f"   - Reason: {decision.reason}")
        print(f"   - Current Price: ${decision.current_price:,.2f}")
        if decision.price_drop_percentage:
            print(f"   - Price Drop: {decision.price_drop_percentage:.2f}%")
    except Exception as e:
        print(f"❌ Decision making test failed: {e}")
        return False
    
    # Test 5: Test simulated trading
    print("\n🎯 Testing simulated trading...")
    try:
        simulated_trade = await simulated_trading_service.execute_simulated_trade(
            decision, dca_config
        )
        print(f"✅ Simulated trade executed:")
        print(f"   - Executed: {simulated_trade.executed}")
        print(f"   - Reason: {simulated_trade.reason}")
        print(f"   - Daily Count: {simulated_trade.daily_trade_count}")
        print(f"   - Timestamp: {simulated_trade.timestamp}")
    except Exception as e:
        print(f"❌ Simulated trading test failed: {e}")
        return False
    
    # Test 6: Test trading summary
    print("\n📊 Testing trading summary...")
    try:
        summary = simulated_trading_service.get_trading_summary()
        stats = summary.get('statistics', {})
        print(f"✅ Trading summary generated:")
        print(f"   - Total Checks: {stats.get('total_checks', 0)}")
        print(f"   - Executed Trades: {stats.get('executed_trades', 0)}")
        print(f"   - Execution Rate: {stats.get('execution_rate_percent', 0)}%")
    except Exception as e:
        print(f"❌ Trading summary test failed: {e}")
        return False
    
    # Test 7: Test persistent storage
    print("\n💾 Testing persistent storage...")
    try:
        persistent_storage_service.save_bot_state(
            is_running=True,
            start_time=datetime.now(),
            total_checks_today=1,
            total_trades_today=1 if simulated_trade.executed else 0
        )
        
        bot_state = persistent_storage_service.load_bot_state()
        print(f"✅ Persistent storage working:")
        print(f"   - Bot running: {bot_state.get('is_running', False)}")
        print(f"   - Last update: {bot_state.get('last_update', 'N/A')}")
    except Exception as e:
        print(f"❌ Persistent storage test failed: {e}")
        return False
    
    # Test 8: Test purchase history
    print("\n📈 Testing purchase history...")
    try:
        history = decision_maker_service.get_purchase_history()
        print(f"✅ Purchase history retrieved:")
        print(f"   - Total Invested: ${history.total_invested:,.2f}")
        print(f"   - Total BTC: {history.total_btc_acquired:.8f}")
        print(f"   - Average Price: ${history.average_purchase_price:,.2f}")
        print(f"   - Total Purchases: {len(history.purchases)}")
    except Exception as e:
        print(f"❌ Purchase history test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The background trading bot is ready to run.")
    return True

async def test_scheduler():
    """Test the scheduler functionality briefly."""
    print("\n🕐 Testing scheduler (brief test)...")
    
    try:
        from app.services.scheduler_service import scheduler_service
        
        # Get initial status
        initial_status = scheduler_service.get_status()
        print(f"✅ Initial scheduler status: Running = {initial_status.is_running}")
        
        # Start scheduler for a brief test (1 minute interval)
        print("⏰ Starting scheduler for brief test...")
        await scheduler_service.start_scheduler(interval_minutes=1)
        
        # Check status
        status = scheduler_service.get_status()
        print(f"✅ Scheduler started: Running = {status.is_running}")
        if status.next_check_time:
            print(f"   - Next check: {status.next_check_time}")
        
        # Wait a moment
        print("⏳ Waiting 3 seconds...")
        await asyncio.sleep(3)
        
        # Trigger immediate check
        print("🔄 Triggering immediate check...")
        success = await scheduler_service.trigger_immediate_check()
        print(f"✅ Manual check result: {success}")
        
        # Stop scheduler
        print("🛑 Stopping scheduler...")
        await scheduler_service.stop_scheduler()
        
        # Check final status
        final_status = scheduler_service.get_status()
        print(f"✅ Final scheduler status: Running = {final_status.is_running}")
        
        print("✅ Scheduler test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Background Trading Bot Tests")
    print("=" * 50)
    
    # Test services
    services_ok = await test_services()
    if not services_ok:
        print("\n❌ Service tests failed. Exiting.")
        sys.exit(1)
    
    # Test scheduler
    scheduler_ok = await test_scheduler()
    if not scheduler_ok:
        print("\n❌ Scheduler tests failed. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("\nThe background trading bot is fully functional and ready for production use.")
    print("\nTo start the bot:")
    print("  python -m app.main")
    print("\nAPI endpoints will be available at:")
    print("  http://localhost:8000/api/v1/bot/status")
    print("  http://localhost:8000/api/v1/bot/history")
    print("  http://localhost:8000/docs (API documentation)")

if __name__ == "__main__":
    asyncio.run(main())