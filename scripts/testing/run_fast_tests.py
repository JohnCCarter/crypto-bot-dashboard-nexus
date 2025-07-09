#!/usr/bin/env python3
"""
Quick test runner for fast tests only.
Usage: python scripts/testing/run_fast_tests.py
"""

import subprocess
import sys
import os

def run_fast_tests():
    """Run only fast tests with parallel execution."""
    # Use the same Python executable that's running this script
    python_exe = sys.executable
    
    cmd = [
        python_exe, "-m", "pytest",
        "-n", "auto",  # Parallel execution
        "-m", "fast",  # Only fast tests
        "-v",          # Verbose output
        "--tb=short",  # Short traceback
        "--color=yes"  # Colored output
    ]
    
    print("🚀 Running fast tests only...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd="backend", check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

def run_api_tests():
    """Run only API tests."""
    # Use the same Python executable that's running this script
    python_exe = sys.executable
    
    cmd = [
        python_exe, "-m", "pytest",
        "-n", "auto",
        "-m", "api",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    print("🌐 Running API tests only...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd="backend", check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        exit_code = run_api_tests()
    else:
        exit_code = run_fast_tests()
    
    sys.exit(exit_code) 