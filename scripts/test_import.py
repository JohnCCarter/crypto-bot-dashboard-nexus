#!/usr/bin/env python3
"""
Test script to isolate import issues in fastapi_app.py
"""

import os
import sys

def test_sys_path():
    """Test the sys.path manipulation from fastapi_app.py"""
    print("=== Testing sys.path manipulation ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Current sys.path[0]: {sys.path[0]}")
    
    # Simulate the sys.path manipulation from fastapi_app.py
    original_path = sys.path.copy()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    
    print(f"Project root added: {project_root}")
    print(f"Project root in sys.path: {project_root in sys.path}")
    
    return original_path

def test_backend_import():
    """Test importing backend modules"""
    print("\n=== Testing backend imports ===")
    
    try:
        # Test basic backend import
        import backend
        print("✅ backend module imported successfully")
        
        # Test backend.api import
        import backend.api
        print("✅ backend.api module imported successfully")
        
        # Test specific API module
        import backend.api.config
        print("✅ backend.api.config imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_fastapi_app_import():
    """Test importing fastapi_app directly"""
    print("\n=== Testing fastapi_app import ===")
    
    try:
        # Test importing the module
        import backend.fastapi_app
        print("✅ backend.fastapi_app imported successfully")
        
        # Test accessing the app
        app = backend.fastapi_app.app
        print("✅ backend.fastapi_app.app accessed successfully")
        
        return True
    except Exception as e:
        print(f"❌ fastapi_app import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting import isolation test...")
    
    # Test 1: sys.path manipulation
    original_path = test_sys_path()
    
    # Test 2: Basic backend imports
    backend_ok = test_backend_import()
    
    # Test 3: fastapi_app import
    fastapi_ok = test_fastapi_app_import()
    
    # Restore original sys.path
    sys.path = original_path
    
    print(f"\n=== Summary ===")
    print(f"Backend imports: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"FastAPI app import: {'✅ OK' if fastapi_ok else '❌ FAILED'}")
    
    if not fastapi_ok:
        print("\n🔍 The issue is likely in the fastapi_app.py import chain")
    else:
        print("\n✅ All imports working - issue may be elsewhere") 