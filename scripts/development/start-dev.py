#!/usr/bin/env python
"""
Utvecklingshjälpskript för att starta FastAPI-servern.
Fungerar på både PowerShell (jobbdator) och Bash (hemdator).
"""

import os
import sys
import subprocess
import platform

print("🚀 Startar utvecklingsmiljön...")

# Detektera om vi använder PowerShell eller Bash
is_powershell = (
    "powershell" in os.environ.get("SHELL", "").lower()
    or platform.system() == "Windows"
)

try:
    # Aktivera virtuell miljö och starta servern
    if is_powershell:
        print("📌 Använder PowerShell")
        subprocess.run(
            "cd backend; python -m uvicorn fastapi_app:app --reload --port 8001",
            shell=True,
        )
    else:
        print("📌 Använder Bash")
        subprocess.run(
            "cd backend && python -m uvicorn fastapi_app:app --reload --port 8001",
            shell=True,
        )

    print("✅ Server startad på port 8001")
except KeyboardInterrupt:
    print("\n🛑 Servern avslutades av användaren")
except Exception as e:
    print(f"❌ Ett fel uppstod: {e}")
    sys.exit(1)
