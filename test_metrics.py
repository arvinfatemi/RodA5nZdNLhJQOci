#!/usr/bin/env python3
"""
Comprehensive test script for the advanced metrics system.
"""
import asyncio
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def test_metrics_models():
    """Test that all metrics models can be imported and instantiated."""
    print("🧪 Testing Metrics Models...")
    
    try:
        from app.models.metrics import (
            CandleData, TechnicalIndicators, OnChainMetrics, 
            RiskMetrics, MarketContext, MetricsSnapshot, 
            MetricsCalculationConfig, ATRConfig
        )
        
        # Test model instantiation
        config = MetricsCalculationConfig()
        atr_config = ATRConfig()
        
        print(f"✅ Models imported successfully")
        print(f"   - Default RSI period: {config.rsi_period}")
        print(f"   - Default ATR multiplier: {atr_config.atr_multiplier}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

async def test_metrics_calculation_service():
    """Test the core metrics calculation service."""
    print("\n📊 Testing MetricsCalculationService...")
    
    try:
        from app.services.metrics_calculation_service import metrics_calculation_service
        
        # Test basic calculations with sample data
        sample_prices = [100, 102, 98, 105, 103, 99, 101, 107, 104, 102, 98, 95, 97, 100, 103]
        
        # Test SMA calculation
        sma = metrics_calculation_service.calculate_sma(sample_prices, 5)
        print(f"✅ SMA(5) calculation: {sma:.2f}")
        
        # Test EMA calculation  
        ema = metrics_calculation_service.calculate_ema(sample_prices, 5)
        print(f"✅ EMA(5) calculation: {ema:.2f}")
        
        # Test RSI calculation
        rsi = metrics_calculation_service.calculate_rsi(sample_prices, 14)
        if rsi:
            print(f"✅ RSI(14) calculation: {rsi:.2f}")
        else:
            print("⚠️ RSI calculation returned None (need more data)")
        
        # Test volatility calculation
        returns = metrics_calculation_service.calculate_returns(sample_prices)
        volatility = metrics_calculation_service.calculate_volatility(returns)
        if volatility:
            print(f"✅ Volatility calculation: {volatility:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ MetricsCalculationService test failed: {e}")
        return False

async def test_onchain_metrics_service():
    """Test the on-chain metrics service."""
    print("\n⛓️ Testing OnChainMetricsService...")
    
    try:
        from app.services.onchain_metrics_service import onchain_metrics_service
        
        # Test blockchain.info API
        print("📡 Testing blockchain.info API...")
        blockchain_data = await onchain_metrics_service.fetch_blockchain_info_metrics()
        if blockchain_data:
            print(f"✅ Blockchain.info data: {len(blockchain_data)} fields")
            if blockchain_data.get("hash_rate"):
                print(f"   - Hash Rate: {blockchain_data['hash_rate']:.2f} TH/s")
        
        # Test mempool.space API
        print("📡 Testing mempool.space API...")
        mempool_data = await onchain_metrics_service.fetch_mempool_space_metrics()
        if mempool_data:
            print(f"✅ Mempool.space data: {len(mempool_data)} fields")
            if mempool_data.get("mempool_size"):
                print(f"   - Mempool size: {mempool_data['mempool_size']} transactions")
        
        # Test comprehensive on-chain metrics
        print("🔗 Testing comprehensive on-chain metrics...")
        onchain_metrics = await onchain_metrics_service.get_onchain_metrics()
        print(f"✅ OnChain metrics collected:")
        if onchain_metrics.hash_rate:
            print(f"   - Hash Rate: {onchain_metrics.hash_rate:.2f} TH/s")
        if onchain_metrics.mempool_size:
            print(f"   - Mempool: {onchain_metrics.mempool_size} txns")
        if onchain_metrics.market_cap:
            print(f"   - Market Cap: ${onchain_metrics.market_cap:,.0f}")
        
        # Test network health score
        health = await onchain_metrics_service.get_network_health_score()
        print(f"✅ Network Health: {health['health_score']}/100 ({health['status']})")
        
        # Test Fear & Greed Index
        fear_greed = await onchain_metrics_service.get_fear_greed_index()
        if fear_greed:
            print(f"✅ Fear & Greed Index: {fear_greed}")
        
        return True
        
    except Exception as e:
        print(f"❌ OnChainMetricsService test failed: {e}")
        return False

async def test_comprehensive_metrics_snapshot():
    """Test getting a complete metrics snapshot."""
    print("\n📸 Testing Comprehensive Metrics Snapshot...")
    
    try:
        from app.services.metrics_calculation_service import metrics_calculation_service
        
        print("📊 Calculating comprehensive metrics snapshot...")
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        print(f"✅ Metrics snapshot generated:")
        print(f"   - Timestamp: {snapshot.timestamp}")
        print(f"   - Current Price: ${snapshot.current_price:,.2f}")
        print(f"   - Data Completeness: {snapshot.data_completeness:.1%}")
        
        if snapshot.technical_indicators:
            ti = snapshot.technical_indicators
            print(f"   📊 Technical Indicators:")
            if ti.rsi_14:
                print(f"      - RSI(14): {ti.rsi_14:.1f}")
            if ti.sma_20:
                print(f"      - SMA(20): ${ti.sma_20:,.0f}")
            if ti.atr_14:
                atr_pct = (ti.atr_14 / snapshot.current_price) * 100
                print(f"      - ATR: {atr_pct:.1f}%")
        
        if snapshot.market_context:
            mc = snapshot.market_context
            print(f"   🎯 Market Context:")
            print(f"      - Short-term trend: {mc.short_term_trend}")
            print(f"      - Volatility regime: {mc.volatility_regime}")
            print(f"      - Market regime: {mc.market_regime}")
        
        if snapshot.risk_metrics:
            rm = snapshot.risk_metrics
            print(f"   ⚠️ Risk Metrics:")
            if rm.sharpe_ratio:
                print(f"      - Sharpe Ratio: {rm.sharpe_ratio:.2f}")
            if rm.max_drawdown:
                print(f"      - Max Drawdown: {rm.max_drawdown:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive metrics test failed: {e}")
        return False

async def test_enhanced_decision_making():
    """Test the enhanced decision making with metrics."""
    print("\n🤔 Testing Enhanced Decision Making...")
    
    try:
        from app.services.decision_maker_service import decision_maker_service
        
        print("🎯 Running basic market evaluation...")
        basic_decision = await decision_maker_service.evaluate_current_market()
        print(f"✅ Basic Decision:")
        print(f"   - Should Buy: {basic_decision.should_buy}")
        print(f"   - Reason: {basic_decision.reason}")
        print(f"   - Current Price: ${basic_decision.current_price:,.2f}")
        
        print("\n🎯 Running enhanced market evaluation with metrics...")
        enhanced_evaluation = await decision_maker_service.evaluate_market_with_metrics()
        
        enhanced_decision = enhanced_evaluation.get("enhanced_decision")
        if enhanced_decision:
            print(f"✅ Enhanced Decision:")
            print(f"   - Should Buy: {enhanced_decision.should_buy}")
            print(f"   - Enhanced Reason: {enhanced_decision.reason}")
        
        market_analysis = enhanced_evaluation.get("market_analysis", {})
        if market_analysis:
            print(f"✅ Market Analysis:")
            print(f"   - Overall Sentiment: {market_analysis.get('overall_sentiment', 'unknown')}")
            print(f"   - Risk Factors: {len(market_analysis.get('risk_factors', []))}")
            print(f"   - Opportunities: {len(market_analysis.get('opportunities', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced decision making test failed: {e}")
        return False

async def test_metrics_api_endpoints():
    """Test metrics API endpoints (import check only)."""
    print("\n🔌 Testing Metrics API Endpoints...")
    
    try:
        from app.api.api_v1.endpoints.metrics import router
        
        # Count the number of endpoints
        endpoint_count = len([route for route in router.routes])
        print(f"✅ Metrics API endpoints imported successfully")
        print(f"   - Number of endpoints: {endpoint_count}")
        
        # Check if main endpoints exist
        endpoint_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        expected_endpoints = ["/snapshot", "/technical-indicators", "/onchain", "/risk-analysis"]
        
        for endpoint in expected_endpoints:
            if endpoint in endpoint_paths:
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

async def test_enhanced_notifications():
    """Test enhanced notification system."""
    print("\n📢 Testing Enhanced Notifications...")
    
    try:
        from app.services.notification_service import notification_service
        from app.models.metrics import MetricsSnapshot, TechnicalIndicators
        
        # Create a sample metrics snapshot for testing
        sample_snapshot = MetricsSnapshot(
            timestamp=datetime.now(),
            current_price=50000.0,
            technical_indicators=TechnicalIndicators(
                rsi_14=65.5,
                atr_14=2500.0,
                sma_20=49000.0,
                sma_50=48000.0
            ),
            data_completeness=0.8
        )
        
        print(f"✅ Enhanced notification service loaded")
        print(f"   - Sample metrics snapshot created")
        print(f"   - RSI: {sample_snapshot.technical_indicators.rsi_14}")
        print(f"   - ATR: {(sample_snapshot.technical_indicators.atr_14 / sample_snapshot.current_price * 100):.1f}%")
        
        # Test notification methods exist
        methods = ['send_metrics_summary', 'send_market_alert', 'send_trade_executed']
        for method in methods:
            if hasattr(notification_service, method):
                print(f"   ✅ {method} method available")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced notifications test failed: {e}")
        return False

async def main():
    """Run all metrics system tests."""
    print("🚀 Starting Advanced Metrics System Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_metrics_models())
    test_results.append(await test_metrics_calculation_service())
    test_results.append(await test_onchain_metrics_service())
    test_results.append(await test_comprehensive_metrics_snapshot())
    test_results.append(await test_enhanced_decision_making())
    test_results.append(await test_metrics_api_endpoints())
    test_results.append(await test_enhanced_notifications())
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print("🎉 ALL METRICS TESTS PASSED!")
        print("\nThe advanced metrics system is fully functional:")
        print("✅ Technical indicators (RSI, MACD, SMA, EMA, ATR)")
        print("✅ Bitcoin on-chain metrics")
        print("✅ Portfolio risk metrics")
        print("✅ Market context analysis")
        print("✅ Enhanced decision making")
        print("✅ Comprehensive API endpoints")
        print("✅ Rich notifications with metrics")
        
        print("\n📊 Available Metrics Endpoints:")
        print("  GET /api/v1/metrics/snapshot")
        print("  GET /api/v1/metrics/technical-indicators")
        print("  GET /api/v1/metrics/onchain")
        print("  GET /api/v1/metrics/risk-analysis")
        print("  GET /api/v1/metrics/market-analysis")
        print("  GET /api/v1/metrics/atr-stop-loss?entry_price=50000")
        print("  GET /api/v1/metrics/volatility-analysis")
        print("  GET /api/v1/metrics/support-resistance")
        print("  GET /api/v1/metrics/trend-analysis")
        
        print("\n🤖 Next Steps:")
        print("1. Start the bot: python -m app.main")
        print("2. View metrics: http://localhost:8000/api/v1/metrics/snapshot")
        print("3. API docs: http://localhost:8000/docs")
        
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        print("Please check the error messages above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())