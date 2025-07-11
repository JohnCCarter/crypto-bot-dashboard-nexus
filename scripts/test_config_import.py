#!/usr/bin/env python3
"""
Test script to isolate the config import issue
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def test_config_import():
    """Test importing config module step by step"""
    print("=== Testing config import chain ===")
    
    try:
        print("1. Testing backend.api import...")
        import backend.api
        print("✅ backend.api imported successfully")
        
        print("2. Testing backend.api.config import...")
        import backend.api.config
        print("✅ backend.api.config imported successfully")
        
        print("3. Testing config router access...")
        router = backend.api.config.router
        print("✅ config router accessed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed at step: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting config import test...")
    success = test_config_import()
    
    if success:
        print("\n✅ Config import chain working correctly")
    else:
        print("\n❌ Config import chain has issues") 