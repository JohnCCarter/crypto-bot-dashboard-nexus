#!/usr/bin/env python3
"""Simple backend starter script."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("🚀 Starting Backend on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)