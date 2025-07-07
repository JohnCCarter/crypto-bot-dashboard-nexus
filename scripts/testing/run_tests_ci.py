#!/usr/bin/env python3
"""
🚀 CI-optimerat Test Runner
Kör tester i optimal ordning för CI/CD pipelines.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Lägg till projektroten i Python-sökvägen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def set_fast_env():
    """Sätt miljövariabler för snabb testning."""
    return {
        "FASTAPI_DISABLE_WEBSOCKETS": "true",
        "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true",
        "FASTAPI_DEV_MODE": "true",
        "PYTHONPATH": str(project_root),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "true"
    }

def run_command(cmd, env=None, description=""):
    """Kör ett kommando och returnera resultat."""
    if env is None:
        env = set_fast_env()
    
    print(f"🚀 {description}")
    print(f"   Kommando: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, env=env, cwd=project_root)
    
    if result.returncode == 0:
        print(f"✅ {description} - KLAR")
    else:
        print(f"❌ {description} - MISSlyckades")
    
    return result.returncode

def run_unit_tests():
    """Kör unit-tester (snabbast)."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "unit",
        "-v",
        "--tb=short",
        "--maxfail=5",
        "--durations=5"
    ]
    return run_command(cmd, description="Unit-tester")

def run_fast_tests():
    """Kör snabba tester."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "fast",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    return run_command(cmd, description="Snabba tester")

def run_mock_tests():
    """Kör mock-tester."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "mock",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    return run_command(cmd, description="Mock-tester")

def run_api_tests():
    """Kör API-tester."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "api",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    return run_command(cmd, description="API-tester")

def run_integration_tests():
    """Kör integration-tester."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/integration/",
        "-v",
        "--tb=short",
        "--maxfail=3"
    ]
    return run_command(cmd, description="Integration-tester")

def run_coverage():
    """Kör tester med coverage."""
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        "-m", "unit or fast or mock",
        "--cov=backend",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=70"
    ]
    return run_command(cmd, description="Coverage-tester")

def main():
    parser = argparse.ArgumentParser(description="CI-optimerat test runner")
    parser.add_argument("--unit-only", action="store_true", help="Kör bara unit-tester")
    parser.add_argument("--fast-only", action="store_true", help="Kör bara snabba tester")
    parser.add_argument("--mock-only", action="store_true", help="Kör bara mock-tester")
    parser.add_argument("--api-only", action="store_true", help="Kör bara API-tester")
    parser.add_argument("--integration-only", action="store_true", help="Kör bara integration-tester")
    parser.add_argument("--coverage", action="store_true", help="Kör med coverage")
    parser.add_argument("--all", action="store_true", help="Kör alla tester i ordning")
    
    args = parser.parse_args()
    
    if args.unit_only:
        return run_unit_tests()
    elif args.fast_only:
        return run_fast_tests()
    elif args.mock_only:
        return run_mock_tests()
    elif args.api_only:
        return run_api_tests()
    elif args.integration_only:
        return run_integration_tests()
    elif args.coverage:
        return run_coverage()
    elif args.all:
        # Kör alla tester i optimal ordning
        print("🚀 CI Test Runner - Kör alla tester i optimal ordning")
        
        # 1. Unit-tester först (snabbast)
        if run_unit_tests() != 0:
            return 1
            
        # 2. Snabba tester
        if run_fast_tests() != 0:
            return 1
            
        # 3. Mock-tester
        if run_mock_tests() != 0:
            return 1
            
        # 4. API-tester
        if run_api_tests() != 0:
            return 1
            
        # 5. Integration-tester sist
        if run_integration_tests() != 0:
            return 1
            
        print("✅ Alla tester klara!")
        return 0
    else:
        # Default: kör unit + fast + mock
        print("🚀 Standard CI Test Runner")
        
        if run_unit_tests() != 0:
            return 1
        if run_fast_tests() != 0:
            return 1
        if run_mock_tests() != 0:
            return 1
            
        print("✅ Standard tester klara!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 