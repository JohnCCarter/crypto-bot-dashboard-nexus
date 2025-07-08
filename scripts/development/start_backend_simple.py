#!/usr/bin/env python3
"""Simple backend starter script."""

import os
import sys
import subprocess

# Add the workspace to Python path
workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, workspace_path)

try:
    print("✅ Starting FastAPI server...")
    print("🚀 Starting FastAPI server on http://localhost:8001")
    
    # Start FastAPI with uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "backend.fastapi_app:app", 
        "--host", "0.0.0.0", 
        "--port", "8001"
    ])
except Exception as e:
    print(f"❌ Error starting backend: {e}")
    import traceback
    traceback.print_exc()
