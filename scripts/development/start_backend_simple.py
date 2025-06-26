#!/usr/bin/env python3
"""Simple backend starter script."""

import os
import sys

# Add the workspace to Python path
workspace_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_path)

try:
    from backend.app import app

    print("✅ Backend app imported successfully")
    print("🚀 Starting Flask server on http://localhost:5001")
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
except Exception as e:
    print(f"❌ Error starting backend: {e}")
    import traceback

    traceback.print_exc()
