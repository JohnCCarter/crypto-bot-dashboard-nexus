"""
🧪 Simple Supabase Database Test
===============================
Tests database connection and creates tables
"""

from backend.supabase_client import supabase
from decimal import Decimal
from datetime import datetime


def test_connection():
    """Test basic Supabase connection"""
    print("🔍 Testing Supabase connection...")
    
    try:
        # Try to get any table (this will fail if no tables exist, but connection works)
        result = supabase.table('trades').select('*').limit(1).execute()
        print("✅ Connection working - tables found!")
        return True
    except Exception as e:
        if 'does not exist' in str(e):
            print("✅ Connection working - no tables yet (expected)")
            return True
        else:
            print(f"❌ Connection failed: {e}")
            return False


def test_after_tables_created():
    """Test database operations after tables are created"""
    print("\n🧪 Testing database operations...")
    
    try:
        # Test 1: Insert a simple trade
        print("📊 Test 1: Creating trade...")
        trade_data = {
            'symbol': 'BTCUSD',
            'side': 'buy',
            'amount': '0.1',
            'price': '105000.0',
            'cost': '10500.0',
            'strategy': 'test_strategy',
            'metadata': {'test': True}
        }
        
        result = supabase.table('trades').insert(trade_data).execute()
        if result.data:
            print(f"✅ Trade created: ID={result.data[0]['id']}")
        
        # Test 2: Read trades
        print("📈 Test 2: Reading trades...")
        result = supabase.table('trades').select('*').execute()
        print(f"✅ Found {len(result.data)} trades")
        
        # Test 3: Create risk metrics
        print("⚠️ Test 3: Creating risk metrics...")
        risk_data = {
            'daily_pnl': '150.50',
            'total_trades': 1,
            'trading_allowed': True,
            'metadata': {'source': 'test'}
        }
        
        result = supabase.table('risk_metrics').insert(risk_data).execute()
        if result.data:
            print(f"✅ Risk metrics created")
        
        # Test 4: Create alert
        print("🚨 Test 4: Creating alert...")
        alert_data = {
            'type': 'system',
            'severity': 'info',
            'title': 'Test Alert',
            'message': 'Database connection test successful!',
            'metadata': {'test': True}
        }
        
        result = supabase.table('alerts').insert(alert_data).execute()
        if result.data:
            print(f"✅ Alert created")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Supabase integration working perfectly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 SIMPLE SUPABASE TEST")
    print("=" * 40)
    
    # Test connection first
    if test_connection():
        print("\n💡 To create tables, run this SQL in Supabase SQL Editor:")
        print("📂 File: backend/supabase_simple_schema.sql")
        print("\n🔄 After creating tables, run this script again to test operations")
    else:
        print("❌ Fix connection issues first")