#!/usr/bin/env python
"""
Pre-commit hook för att säkerställa kodkvalitet innan commit.
"""
import os
import sys
import subprocess

def main():
    """
    Huvudfunktion för pre-commit hook.
    """
    print("✅ Pre-commit hook körs...")
    
    # Här kan du lägga till kontroller som:
    # - Kör linters
    # - Kör tester
    # - Kontrollera formatering
    # osv.
    
    # För tillfället gör vi ingenting och låter commiten fortsätta
    return 0

if __name__ == "__main__":
    sys.exit(main()) 