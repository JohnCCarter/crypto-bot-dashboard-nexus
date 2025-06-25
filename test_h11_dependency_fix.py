#!/usr/bin/env python3
"""
Test script to verify h11 dependency fix in requirements.txt

This script validates that:
1. The h11 version specification is syntactically correct
2. The version range allows patch updates within 0.16.x series
3. The version range excludes potentially incompatible versions
"""

import sys
from packaging.specifiers import SpecifierSet


def test_h11_version_specification():
    """Test the h11 version specification from requirements.txt"""
    
    # The new specification we implemented
    h11_spec = ">=0.16.0,<0.17.0"
    
    try:
        spec = SpecifierSet(h11_spec)
        print(f"✓ h11 version specification '{h11_spec}' is valid")
        
        # Test cases: versions that should be included
        should_include = [
            "0.16.0",  # Original version
            "0.16.1",  # Patch update
            "0.16.2",  # Another patch update
            "0.16.10", # Higher patch version
        ]
        
        # Test cases: versions that should be excluded
        should_exclude = [
            "0.15.9",  # Older minor version
            "0.17.0",  # Next minor version
            "0.17.1",  # Future version
            "1.0.0",   # Major version bump
        ]
        
        print(f"\nTesting version inclusion:")
        for version in should_include:
            if version in spec:
                print(f"  ✓ {version} is included (correct)")
            else:
                print(f"  ✗ {version} is excluded (ERROR)")
                return False
        
        print(f"\nTesting version exclusion:")
        for version in should_exclude:
            if version not in spec:
                print(f"  ✓ {version} is excluded (correct)")
            else:
                print(f"  ✗ {version} is included (ERROR)")
                return False
        
        print(f"\n✓ All version specification tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Invalid version specification: {e}")
        return False


def verify_requirements_file():
    """Verify the requirements.txt file contains the corrected h11 specification"""
    
    requirements_path = "backend/requirements.txt"
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        # Check if the old problematic line is gone
        if "h11==0.16.0" in content:
            print(f"✗ Found old h11==0.16.0 specification in {requirements_path}")
            return False
        
        # Check if the new specification is present
        if "h11>=0.16.0,<0.17.0" in content:
            print(f"✓ Found corrected h11>=0.16.0,<0.17.0 specification in {requirements_path}")
            return True
        else:
            print(f"✗ Could not find h11>=0.16.0,<0.17.0 specification in {requirements_path}")
            return False
            
    except FileNotFoundError:
        print(f"✗ Could not find {requirements_path}")
        return False
    except Exception as e:
        print(f"✗ Error reading {requirements_path}: {e}")
        return False


def main():
    """Run all tests"""
    print("=== H11 Dependency Fix Verification ===\n")
    
    print("1. Testing version specification syntax:")
    spec_test = test_h11_version_specification()
    
    print("\n2. Verifying requirements.txt file:")
    file_test = verify_requirements_file()
    
    print(f"\n=== Results ===")
    if spec_test and file_test:
        print("✓ All tests passed! The h11 dependency conflict fix is correct.")
        print("\nThe change from 'h11==0.16.0' to 'h11>=0.16.0,<0.17.0' allows:")
        print("  - Installation of h11 0.16.0 (the original version)")
        print("  - Installation of compatible patch versions (0.16.1, 0.16.2, etc.)")
        print("  - Exclusion of potentially incompatible future versions (0.17.0+)")
        print("\nThis should resolve the CI/CD dependency conflict.")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())