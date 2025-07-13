#!/usr/bin/env python3
"""
🚀 Optimerad Test Runner
Kör tester med maximal prestanda genom parallell exekvering och smart kategorisering.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Lägg till projektroten i Python-sökvägen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_tests_with_parallel(category=None, markers=None, max_workers="auto"):
    """Kör tester parallellt med optimerade inställningar."""
    
    # Sätt miljövariabler för snabbare testning
    env = os.environ.copy()
    env.update({
        "FASTAPI_DISABLE_WEBSOCKETS": "true",
        "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true", 
        "FASTAPI_DEV_MODE": "true",
        "PYTHONPATH": str(project_root),
    })
    
    # Bygg kommandot
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests/",
        # "-n", str(max_workers),  # Ta bort denna rad eftersom det redan finns i pytest.ini
        "-v",
        "--tb=short",
        "--durations=10",
        "--durations-min=0.5",
        "--maxfail=5",
        "--color=yes",
        "--disable-warnings"
    ]
    
    # Lägg till markers om specificerade
    if markers:
        cmd.extend(["-m", markers])
    
    # Lägg till kategori om specificerad
    if category:
        cmd.extend(["-k", category])
    
    print(f"🚀 Kör tester parallellt med {max_workers} workers...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, env=env, cwd=project_root)
        end_time = time.time()
        
        print(f"\n⏱️  Testtid: {end_time - start_time:.2f} sekunder")
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

def run_fast_tests_only():
    """Kör bara snabba tester parallellt."""
    print("⚡ Kör bara snabba tester...")
    return run_tests_with_parallel(
        markers="fast or unit or api or mock",
        max_workers="auto"
    )

def run_slow_tests_only():
    """Kör bara långsamma tester parallellt."""
    print("🐌 Kör långsamma tester...")
    return run_tests_with_parallel(
        markers="slow or positions or config or risk or portfolio",
        max_workers="2"  # Färre workers för långsamma tester
    )

def run_all_tests_optimized():
    """Kör alla tester i optimerad ordning."""
    print("🚀 Optimerad Test Runner - Kör alla tester i optimal ordning")
    
    # 1. Snabba tester först (parallellt)
    print("\n" + "="*60)
    print("STEG 1: Snabba tester")
    print("="*60)
    if run_fast_tests_only() != 0:
        print("❌ Snabba tester misslyckades")
        return 1
    
    # 2. Långsamma tester sist (parallellt, men färre workers)
    print("\n" + "="*60)
    print("STEG 2: Långsamma tester")
    print("="*60)
    if run_slow_tests_only() != 0:
        print("❌ Långsamma tester misslyckades")
        return 1
    
    print("\n✅ Alla tester klara!")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Optimerad test runner")
    parser.add_argument("--fast-only", action="store_true", help="Kör bara snabba tester")
    parser.add_argument("--slow-only", action="store_true", help="Kör bara långsamma tester")
    parser.add_argument("--workers", type=str, default="auto", help="Antal parallella workers (auto, 1, 2, 4, etc)")
    parser.add_argument("--category", type=str, help="Kör tester som matchar kategori (t.ex. 'positions', 'risk')")
    parser.add_argument("--markers", type=str, help="Kör tester med specifika markers (t.ex. 'fast or api')")
    
    args = parser.parse_args()
    
    if args.fast_only:
        return run_fast_tests_only()
    elif args.slow_only:
        return run_slow_tests_only()
    elif args.category:
        return run_tests_with_parallel(category=args.category, max_workers=args.workers)
    elif args.markers:
        return run_tests_with_parallel(markers=args.markers, max_workers=args.workers)
    else:
        return run_all_tests_optimized()

if __name__ == "__main__":
    sys.exit(main()) 