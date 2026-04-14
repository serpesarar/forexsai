#!/usr/bin/env python3
"""
MT5 Redis Bridge Data Flow Diagnostic Script
Checks if data is flowing correctly from MT5 -> Redis -> DataHub
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

# Configuration
RAILWAY_API_URL = "https://upbeat-flow-production.up.railway.app"
LOCAL_API_URL = "http://localhost:8000"

# Try local first, then Railway
API_BASE = LOCAL_API_URL

async def check_datahub_flow_check() -> Dict[str, Any]:
    """Check DataHub flow-check endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/api/datahub/flow-check")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

async def check_datahub_status() -> Dict[str, Any]:
    """Check DataHub status endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/api/datahub/status")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

async def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connectivity."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/api/health/redis")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

async def check_websocket_stats() -> Dict[str, Any]:
    """Check WebSocket connection stats."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/api/ws/stats")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

def analyze_flow_check(flow_data: Dict[str, Any]) -> list:
    """Analyze flow-check data and return issues found."""
    issues = []
    
    if "error" in flow_data:
        issues.append(f"❌ API Error: {flow_data['error']}")
        return issues
    
    market_source = flow_data.get("market_data_source", "unknown")
    print(f"\n📊 Market Data Source: {market_source}")
    
    if market_source == "eodhd":
        issues.append("⚠️  WARNING: Using EODHD mode (not MT5/Redis)")
    elif market_source == "hybrid":
        print("✅ Hybrid mode active (EODHD + MT5 Redis)")
    elif market_source == "mt5_redis":
        print("✅ MT5 Redis mode active")
    
    if not flow_data.get("running", False):
        issues.append("❌ DataHub is NOT running!")
    else:
        print("✅ DataHub is running")
    
    symbols = flow_data.get("symbols", {})
    if not symbols:
        issues.append("❌ No symbol data available")
        return issues
    
    print(f"\n📈 Symbol Reports ({len(symbols)} symbols):")
    print("-" * 80)
    
    for symbol, report in symbols.items():
        print(f"\n🔹 {symbol}:")
        
        # Price check
        price_available = report.get("price_available", False)
        price_source = report.get("price_source", "unknown")
        price_age = report.get("price_age_seconds", 9999)
        
        if not price_available:
            issues.append(f"❌ {symbol}: No price available")
        elif price_age > 300:
            issues.append(f"⚠️  {symbol}: Price stale ({price_age:.0f}s old)")
        else:
            print(f"   ✅ Price: {price_source} (age: {price_age:.0f}s)")
        
        # Timeframe checks
        timeframes = report.get("timeframes", {})
        for tf in ["5m", "1h", "eod"]:
            tf_data = timeframes.get(tf, {})
            available = tf_data.get("available", False)
            count = tf_data.get("count", 0)
            source = tf_data.get("source", "unknown")
            age = tf_data.get("cache_age_seconds", 9999)
            
            if not available:
                issues.append(f"❌ {symbol}/{tf}: Not available")
            elif count < 3:
                issues.append(f"⚠️  {symbol}/{tf}: Only {count} candles")
            elif age > 600:
                issues.append(f"⚠️  {symbol}/{tf}: Stale data ({age:.0f}s)")
            else:
                print(f"   ✅ {tf}: {count} candles, {source} (age: {age:.0f}s)")
        
        # Analysis readiness
        if not report.get("analysis_ready", False):
            issues.append(f"⚠️  {symbol}: Not analysis-ready")
    
    return issues

async def monitor_price_stream(duration_seconds: int = 10):
    """Monitor price updates via WebSocket for a short duration."""
    print(f"\n🔴 Monitoring WebSocket price stream for {duration_seconds}s...")
    print("(This checks if live prices are actually flowing)")
    
    try:
        import websockets
        
        uri = f"ws://localhost:8000/ws/all"
        prices_seen: Dict[str, list] = {}
        
        async with websockets.connect(uri) as ws:
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    
                    if data.get("type") == "price_update":
                        symbol = data.get("symbol")
                        price = data.get("price")
                        source = data.get("source", "unknown")
                        
                        if symbol not in prices_seen:
                            prices_seen[symbol] = []
                        prices_seen[symbol].append({"price": price, "source": source})
                        
                except asyncio.TimeoutError:
                    continue
        
        print(f"\n📡 Price Updates Received ({duration_seconds}s window):")
        for symbol, updates in prices_seen.items():
            print(f"   {symbol}: {len(updates)} updates (source: {updates[0]['source']})")
            if len(updates) >= 2:
                price_change = updates[-1]['price'] - updates[0]['price']
                print(f"      Price change: {price_change:.2f}")
        
        if not prices_seen:
            print("   ⚠️  No price updates received!")
            
    except ImportError:
        print("   ℹ️  websockets package not installed, skipping live stream test")
    except Exception as e:
        print(f"   ❌ WebSocket error: {e}")

async def main():
    """Run all diagnostics."""
    print("=" * 80)
    print("MT5 Redis Bridge Data Flow Diagnostic")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)
    
    global API_BASE
    
    # Try to connect to local first
    print(f"\n🌐 Testing API connectivity...")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.get(f"{LOCAL_API_URL}/api/health")
        print(f"   ✅ Local API found at {LOCAL_API_URL}")
    except:
        print(f"   ❌ Local API not available, trying Railway...")
        API_BASE = RAILWAY_API_URL
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"{RAILWAY_API_URL}/api/health")
            print(f"   ✅ Railway API found at {RAILWAY_API_URL}")
        except Exception as e:
            print(f"   ❌ Cannot connect to Railway API: {e}")
            sys.exit(1)
    
    # Run checks
    print(f"\n{'='*80}")
    print("1️⃣  DataHub Flow Check")
    print("=" * 80)
    flow_data = await check_datahub_flow_check()
    issues = analyze_flow_check(flow_data)
    
    print(f"\n{'='*80}")
    print("2️⃣  DataHub Status")
    print("=" * 80)
    status_data = await check_datahub_status()
    if "error" in status_data:
        print(f"   ❌ Error: {status_data['error']}")
    else:
        print(f"   Running: {status_data.get('running', False)}")
        print(f"   Source: {status_data.get('market_data_source', 'unknown')}")
        print(f"   Symbols tracked: {status_data.get('symbols', [])}")
        prices = status_data.get('prices', {})
        if prices:
            print(f"   Current prices:")
            for sym, price in prices.items():
                if price:
                    print(f"      {sym}: {price}")
    
    print(f"\n{'='*80}")
    print("3️⃣  Redis Connection")
    print("=" * 80)
    redis_data = await check_redis_connection()
    print(f"   {json.dumps(redis_data, indent=2)}")
    
    print(f"\n{'='*80}")
    print("4️⃣  WebSocket Stats")
    print("=" * 80)
    ws_data = await check_websocket_stats()
    print(f"   {json.dumps(ws_data, indent=2)}")
    
    # Live stream test (only if local)
    if API_BASE == LOCAL_API_URL:
        print(f"\n{'='*80}")
        await monitor_price_stream(duration_seconds=10)
    
    # Summary
    print(f"\n{'='*80}")
    print("📋 SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"\n⚠️  Issues Found ({len(issues)}):")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ All checks passed! Bridge appears to be working correctly.")
    
    # Specific MT5 Redis checks
    market_source = flow_data.get("market_data_source", "unknown")
    if market_source in ["mt5_redis", "hybrid"]:
        print(f"\n🔍 MT5 Redis Specific Checks:")
        
        # Check for MT5 Redis source in prices
        prices = flow_data.get("symbols", {})
        mt5_prices = 0
        eodhd_prices = 0
        
        for symbol, report in prices.items():
            price_source = report.get("price_source", "")
            if "mt5" in price_source.lower():
                mt5_prices += 1
            elif "eodhd" in price_source.lower():
                eodhd_prices += 1
        
        print(f"   MT5-sourced prices: {mt5_prices}")
        print(f"   EODHD-sourced prices: {eodhd_prices}")
        
        if market_source == "mt5_redis" and mt5_prices == 0:
            print("   ❌ WARNING: MT5 Redis mode but no MT5-sourced prices found!")
            print("      - Check if MT5 EA is running and publishing to Redis")
            print("      - Check if REDIS_URL is correctly configured")
            print("      - Check Railway logs: railway logs --tail")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
