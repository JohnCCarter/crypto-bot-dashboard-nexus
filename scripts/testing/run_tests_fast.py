#!/usr/bin/env python3
"""
🚀 Snabb Test Runner
Kör tester med optimerade inställningar för snabbare feedback.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Lägg till projektroten i Python-sökvägen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_fast_tests():
    """Kör snabba tester först."""
    print("🚀 Kör snabba tester...")
    
    # Sätt miljövariabler för snabbare testning
    env = os.environ.copy()
    env.update({
        "FASTAPI_DISABLE_WEBSOCKETS": "true",
        "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true", 
        "FASTAPI_DEV_MODE": "true",
        "PYTHONPATH": str(project_root)
    })
    
    # Kör unit-tester först (snabbast)
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "unit or fast",
        "-v",
        "--tb=short",
        "--maxfail=10",
        "--durations=10"
    ]
    
    result = subprocess.run(cmd, env=env, cwd=project_root)
    return result.returncode

def run_mock_tests():
    """Kör mock-tester."""
    print("🎭 Kör mock-tester...")
    
    env = os.environ.copy()
    env.update({
        "FASTAPI_DISABLE_WEBSOCKETS": "true",
        "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true",
        "FASTAPI_DEV_MODE": "true",
        "PYTHONPATH": str(project_root)
    })
    
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "mock",
        "-v",
        "--tb=short",
        "--maxfail=10"
    ]
    
    result = subprocess.run(cmd, env=env, cwd=project_root)
    return result.returncode

def run_api_tests():
    """Kör API-tester."""
    print("🌐 Kör API-tester...")
    
    env = os.environ.copy()
    env.update({
        "FASTAPI_DISABLE_WEBSOCKETS": "true",
        "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true",
        "FASTAPI_DEV_MODE": "true",
        "PYTHONPATH": str(project_root)
    })
    
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "api",
        "-v",
        "--tb=short",
        "--maxfail=10"
    ]
    
    result = subprocess.run(cmd, env=env, cwd=project_root)
    return result.returncode

def run_slow_tests():
    """Kör långsamma tester sist."""
    print("🐌 Kör långsamma tester...")
    
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(project_root)
    })
    
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "slow or integration or e2e",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    
    result = subprocess.run(cmd, env=env, cwd=project_root)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Snabb test runner")
    parser.add_argument("--fast-only", action="store_true", help="Kör bara snabba tester")
    parser.add_argument("--mock-only", action="store_true", help="Kör bara mock-tester")
    parser.add_argument("--api-only", action="store_true", help="Kör bara API-tester")
    parser.add_argument("--slow-only", action="store_true", help="Kör bara långsamma tester")
    
    args = parser.parse_args()
    
    if args.fast_only:
        return run_fast_tests()
    elif args.mock_only:
        return run_mock_tests()
    elif args.api_only:
        return run_api_tests()
    elif args.slow_only:
        return run_slow_tests()
    else:
        # Kör alla tester i optimerad ordning
        print("🚀 Snabb Test Runner - Kör alla tester i optimerad ordning")
        
        # 1. Snabba tester först
        if run_fast_tests() != 0:
            print("❌ Snabba tester misslyckades")
            return 1
            
        # 2. Mock-tester
        if run_mock_tests() != 0:
            print("❌ Mock-tester misslyckades")
            return 1
            
        # 3. API-tester
        if run_api_tests() != 0:
            print("❌ API-tester misslyckades")
            return 1
            
        # 4. Långsamma tester sist
        if run_slow_tests() != 0:
            print("❌ Långsamma tester misslyckades")
            return 1
            
        print("✅ Alla tester klara!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 