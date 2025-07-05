#!/usr/bin/env python
"""
Start-dev script för att starta utvecklingsmiljön.
Fungerar i både PowerShell och Bash.
"""

import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path


def is_powershell():
    """Kontrollerar om skriptet körs i PowerShell."""
    return "POWERSHELL_DISTRIBUTION_CHANNEL" in os.environ


def is_bash():
    """Kontrollerar om skriptet körs i Bash."""
    return "BASH" in os.environ or os.environ.get("SHELL", "").endswith("bash")


def is_work_computer():
    """
    Detekterar om skriptet körs på jobbdatorn baserat på datornamn.
    """
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn på jobbet
    return "work" in hostname or "job" in hostname


def is_home_computer():
    """
    Detekterar om skriptet körs på hemdatorn baserat på datornamn.
    """
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn hemma
    return "skynet" in hostname or "home" in hostname


def get_python_path():
    """Returnerar sökvägen till Python-exekverbara filen."""
    return sys.executable


def run_command(command, shell=True, background=False):
    """Kör ett kommando i terminalen."""
    print(f"Kör kommando: {command}")
    
    if background:
        if is_powershell():
            # För PowerShell använder vi en annan metod som fungerar bättre
            subprocess.Popen(["powershell", "-Command", command], shell=False)
        else:
            # För Bash använder vi & för att köra i bakgrunden
            subprocess.Popen(f"{command} &", shell=True)
    else:
        return subprocess.run(command, shell=shell, check=False)


def activate_venv():
    """Aktiverar virtuell miljö."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Virtuell miljö saknas. Skapar en ny...")
        python_path = get_python_path()
        run_command(f"{python_path} -m venv venv")
    
    if is_powershell():
        return "venv\\Scripts\\Activate.ps1"
    else:
        return "source venv/Scripts/activate"


def main():
    """Huvudfunktion för att starta utvecklingsmiljön."""
    # Få absolut sökväg till projektets rot
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    print(f"Projektets rot: {project_root}")
    
    print("Startar utvecklingsmiljön...")
    print(f"OS: {platform.system()}")
    print(f"PowerShell: {is_powershell()}")
    print(f"Bash: {is_bash()}")
    print(f"Python: {get_python_path()}")
    print(f"Datornamn: {socket.gethostname()}")
    
    if is_work_computer():
        print("Detekterad miljö: JOBBDATOR")
    elif is_home_computer():
        print("Detekterad miljö: HEMDATOR")
    else:
        print("Detekterad miljö: OKÄND")
        
    # Fråga användaren om miljön är korrekt detekterad
    if not is_work_computer() and not is_home_computer():
        choice = input("Är detta din jobbdator? (j/n): ")
        if choice.lower() == "j":
            print("Använder jobbdatorns inställningar")
        else:
            print("Använder hemdatorns inställningar")
    
    # Aktivera virtuell miljö
    activate_cmd = activate_venv()
    
    # Starta backend (Flask) - kör från projektets rot för att lösa importfel
    if is_powershell():
        backend_cmd = (
            f"{activate_cmd}; "
            f"cd {project_root}; "
            f"python -m backend.app"
        )
    else:
        backend_cmd = (
            f"{activate_cmd} && "
            f"cd {project_root} && "
            f"python -m backend.app"
        )
    
    run_command(backend_cmd, background=True)
    print("Backend (Flask) startat på port 5000")
    
    # Vänta lite för att låta backend starta
    time.sleep(2)
    
    # Starta backend (FastAPI) - kör från projektets rot för att lösa importfel
    if is_powershell():
        fastapi_cmd = (
            f"{activate_cmd}; "
            f"cd {project_root}; "
            f"python -m backend.fastapi_app"
        )
    else:
        fastapi_cmd = (
            f"{activate_cmd} && "
            f"cd {project_root} && "
            f"python -m backend.fastapi_app"
        )
    
    run_command(fastapi_cmd, background=True)
    print("Backend (FastAPI) startat på port 8001")
    
    # Vänta lite för att låta backend starta
    time.sleep(2)
    
    # Starta frontend
    if is_powershell():
        frontend_cmd = (
            f"{activate_cmd}; "
            f"cd {project_root}; "
            f"npm run dev"
        )
    else:
        frontend_cmd = (
            f"{activate_cmd} && "
            f"cd {project_root} && "
            f"npm run dev"
        )
    
    run_command(frontend_cmd, background=True)
    print("Frontend startat")
    
    print("\nUtvecklingsmiljön är nu igång!")
    print("- Backend (Flask): http://localhost:5000")
    print("- Backend (FastAPI): http://localhost:8001")
    print("- Frontend: http://localhost:5173")
    
    print("\nTryck Ctrl+C för att avsluta alla processer.")
    
    try:
        # Håll skriptet igång så att användaren kan avbryta med Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nAvslutar utvecklingsmiljön...")


if __name__ == "__main__":
    main()
