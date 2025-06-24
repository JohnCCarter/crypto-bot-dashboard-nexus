#!/usr/bin/env python3
"""
Robust backend startup script that prevents duplicate processes.
This solves the recurring problem of multiple app_integrated processes.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

def kill_existing_processes():
    """Kill any existing app_integrated processes."""
    try:
        # Kill processes by name
        subprocess.run(["pkill", "-f", "app_integrated"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        print("🔄 Stopped existing backend processes")
        time.sleep(2)  # Give processes time to shut down
        
        # Verify they're gone
        result = subprocess.run(["pgrep", "-f", "app_integrated"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("⚠️  Some processes still running, force killing...")
            subprocess.run(["pkill", "-9", "-f", "app_integrated"],
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            time.sleep(1)
            
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")

def check_port_availability(port=5000):
    """Check if port is available."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            return result != 0  # Port available if connection fails
    except:
        return True

def start_backend():
    """Start the backend process."""
    # Ensure we're in the right directory
    os.chdir('/workspace')
    
    # Activate virtual environment
    venv_python = '/workspace/venv/bin/python'
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found at /workspace/venv/")
        return False
    
    # Start the process
    env = os.environ.copy()
    env['PYTHONPATH'] = '/workspace'
    
    try:
        print("🚀 Starting backend with single process...")
        # Use exec to replace current process, preventing duplicates
        os.execve(venv_python, [venv_python, '-m', 'backend.app_integrated'], env)
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def main():
    """Main startup routine."""
    print("🔍 Backend Startup - Robust Mode")
    print("=" * 40)
    
    # Step 1: Kill existing processes
    kill_existing_processes()
    
    # Step 2: Check port availability
    if not check_port_availability():
        print("❌ Port 5000 still in use after cleanup")
        # Try to kill whatever is using the port
        try:
            subprocess.run(["fuser", "-k", "5000/tcp"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            time.sleep(2)
        except:
            pass
    
    # Step 3: Final verification
    if not check_port_availability():
        print("❌ Cannot free port 5000. Manual intervention required.")
        sys.exit(1)
    
    print("✅ Port 5000 available")
    print("✅ Environment ready")
    
    # Step 4: Start backend (this will replace current process)
    start_backend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)