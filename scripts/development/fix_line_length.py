#!/usr/bin/env python3
"""
Script to automatically fix E501 (line too long) issues.
This script uses Black with specific line length to fix formatting.
"""

import subprocess
import sys
from pathlib import Path


def fix_line_length_issues():
    """Fix line length issues using Black formatter."""
    backend_path = Path(__file__).parent.parent.parent / "backend"
    
    print("🔧 Fixing line length issues with Black...")
    
    try:
        # Run Black with line length 88 (flake8 compatible)
        result = subprocess.run([
            "black", 
            "--line-length", "88",
            str(backend_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Black formatting completed successfully")
            print(result.stdout)
        else:
            print("❌ Black formatting failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Black not found. Please install: pip install black")
        return False
        
    return True


def check_remaining_issues():
    """Check for remaining flake8 E501 issues."""
    backend_path = Path(__file__).parent.parent.parent / "backend"
    
    print("\n🔍 Checking for remaining line length issues...")
    
    try:
        result = subprocess.run([
            "flake8",
            str(backend_path),
            "--select=E501",
            "--max-line-length=88"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ No line length issues remaining!")
            return True
        else:
            print("⚠️ Some E501 issues remain:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("❌ Flake8 not found. Please install: pip install flake8")
        return False


if __name__ == "__main__":
    print("🚀 Starting automatic line length fix...")
    
    # Fix line length issues
    if fix_line_length_issues():
        # Check if issues remain
        check_remaining_issues()
    
    print("\n✅ Line length fix process completed!") 