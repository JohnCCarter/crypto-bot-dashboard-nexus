#!/usr/bin/env python3
"""
Integration test runner for comprehensive testing.
Usage: python scripts/testing/run_integration_tests.py
"""

import subprocess
import sys
import os

def run_integration_tests():
    """Run only integration tests with parallel execution."""
    # Use the same Python executable that's running this script
    python_exe = sys.executable
    
    cmd = [
        python_exe, "-m", "pytest",
        "-n", "auto",  # Parallel execution
        "-m", "integration",  # Only integration tests
        "-v",          # Verbose output
        "--tb=short",  # Short traceback
        "--color=yes"  # Colored output
    ]
    
    print("🔗 Running integration tests only...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    print("⚠️  Note: Integration tests require backend server to be running!")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd="backend", check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

def run_all_tests():
    """Run all tests (unit + integration)."""
    python_exe = sys.executable
    
    cmd = [
        python_exe, "-m", "pytest",
        "-n", "auto",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    print("🧪 Running all tests (unit + integration)...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd="backend", check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

def run_slow_tests():
    """Run only slow tests (usually integration + e2e)."""
    python_exe = sys.executable
    
    cmd = [
        python_exe, "-m", "pytest",
        "-n", "auto",
        "-m", "slow",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    print("🐌 Running slow tests only...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    print("⚠️  Note: Slow tests may take a while to complete!")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd="backend", check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            exit_code = run_all_tests()
        elif sys.argv[1] == "slow":
            exit_code = run_slow_tests()
        else:
            print("Usage:")
            print("  python scripts/testing/run_integration_tests.py          # Run integration tests")
            print("  python scripts/testing/run_integration_tests.py all      # Run all tests")
            print("  python scripts/testing/run_integration_tests.py slow     # Run slow tests")
            sys.exit(1)
    else:
        exit_code = run_integration_tests()
    
    sys.exit(exit_code) 