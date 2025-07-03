#!/usr/bin/env python
"""
FastAPI Development Server med stöd för olika konfigurationslägen.

Detta skript startar FastAPI-servern med anpassade konfigurationer baserat på vad du
arbetar med för att optimera resurser och minimera CPU-användning.
"""

import os
import sys
import argparse
import subprocess
import platform

# Lägg till projektroten i Python-sökvägen
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)


def is_powershell():
    """Kontrollera om skriptet körs i PowerShell."""
    return platform.system() == "Windows"


def run_command(command):
    """Kör ett kommando och dirigera output till terminal."""
    if is_powershell():
        # PowerShell använder ; för att separera kommandon
        if isinstance(command, list):
            command = " ; ".join(command)
        subprocess.run(command, shell=True)
    else:
        # Bash använder && för att separera kommandon
        if isinstance(command, list):
            command = " && ".join(command)
        subprocess.run(command, shell=True)


def create_env_file(mode, reload_enabled=True):
    """Skapa en .env.fastapi_dev fil med konfigurationsvariabler."""
    env_path = os.path.join(project_root, ".env.fastapi_dev")
    
    # Basvariabler
    env_vars = {
        "FASTAPI_NO_RELOAD": str(not reload_enabled).lower(),
        "FASTAPI_DEV_MODE": "true",  # Alltid i dev-läge när vi använder detta skript
    }
    
    # Lägg till mode-specifika variabler
    if mode == "minimal":
        env_vars.update({
            "FASTAPI_DISABLE_WEBSOCKETS": "true",
            "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true",
        })
    elif mode == "api":
        env_vars.update({
            "FASTAPI_DISABLE_WEBSOCKETS": "true",
            "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "false",
        })
    elif mode == "websocket":
        env_vars.update({
            "FASTAPI_DISABLE_WEBSOCKETS": "false",
            "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "true",
        })
    elif mode == "full":
        env_vars.update({
            "FASTAPI_DISABLE_WEBSOCKETS": "false",
            "FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER": "false",
        })
    
    # Skriv till fil
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"📝 Laddar anpassade inställningar från: {os.path.abspath(env_path)}")
    return env_path


def main():
    """Huvudfunktion för att starta FastAPI-servern i olika lägen."""
    parser = argparse.ArgumentParser(description="Starta FastAPI-servern i olika utvecklingslägen")
    parser.add_argument("--mode", "-m", choices=["minimal", "api", "websocket", "full"], 
                        default="minimal", help="Utvecklingsläge")
    parser.add_argument("--no-reload", action="store_true", 
                        help="Inaktivera hot reload (lägre CPU-användning)")
    parser.add_argument("--port", "-p", type=int, default=8001, 
                        help="Port för FastAPI-servern")
    
    args = parser.parse_args()
    
    # Visa konfiguration
    if args.mode == "minimal":
        print("🔧 Minimal konfiguration: WebSockets och GlobalNonceManager inaktiverade")
    elif args.mode == "api":
        print("🔧 API-konfiguration: WebSockets inaktiverade, GlobalNonceManager aktiverad")
    elif args.mode == "websocket":
        print("🔧 WebSocket-konfiguration: WebSockets aktiverade, GlobalNonceManager inaktiverad")
    else:
        print("🔧 Full konfiguration: Alla komponenter aktiverade")
    
    print(f"🔌 Port: {args.port}, Reload: {not args.no_reload}")
    
    # Skapa .env.fastapi_dev fil
    env_file = create_env_file(args.mode, not args.no_reload)
    
    # Starta FastAPI-servern med rätt konfiguration
    os.environ["FASTAPI_ENV_FILE"] = env_file
    
    # Kör direkt med Python istället för att använda run_command
    # Detta löser problem med sökvägar i Windows
    os.chdir(project_root)
    
    # Bygg kommandot - hantera reload-flaggan korrekt
    cmd = f"python -m uvicorn backend.fastapi_app:app --host 0.0.0.0 --port {args.port}"
    
    # Hantera reload-flaggan korrekt - uvicorn använder --reload som en flagga utan värde
    if not args.no_reload:
        cmd += " --reload"
    
    # Kör kommandot direkt
    print(f"\n🚀 Kör: {cmd}\n")
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    main() 