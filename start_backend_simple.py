#!/usr/bin/env python3
"""Simple backend starter script."""

import sys
import os

# Add the workspace to Python path
workspace_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_path)

try:
    from backend.app import app
    print("✅ Backend app imported successfully")
    print("🚀 Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
except Exception as e:
    print(f"❌ Error starting backend: {e}")
    import traceback
    traceback.print_exc()