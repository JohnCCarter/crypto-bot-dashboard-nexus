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
    else:
        # Bash använder && för att separera kommandon
        if isinstance(command, list):
            command = " && ".join(command)
            
    print(f"\n🚀 Kör: {command}\n")
    subprocess.run(command, shell=True)


def create_env_file(env_vars):
    """Skapa en temporär .env-fil med angivna miljövariabler."""
    env_file_path = os.path.join(project_root, ".env.fastapi_dev")
    with open(env_file_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    return env_file_path


def main():
    parser = argparse.ArgumentParser(description="Starta FastAPI-servern med olika konfigurationsalternativ")
    
    parser.add_argument(
        "--mode", 
        choices=["full", "api", "websocket", "minimal"],
        default="minimal",
        help=(
            "Utvecklingsläge: "
            "'full'=alla tjänster aktiverade, "
            "'api'=endast API utan WebSockets, "
            "'websocket'=API med WebSockets, "
            "'minimal'=minimalt läge utan WebSockets eller GlobalNonceManager"
        )
    )
    
    parser.add_argument(
        "--no-reload", 
        action="store_true",
        help="Inaktivera hot reload (reducerar CPU-användning betydligt)"
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        default=8001,
        help="Port för FastAPI-servern"
    )
    
    args = parser.parse_args()
    
    # Skapa miljövariabler baserat på valt läge
    env_vars = {
        "FASTAPI_PORT": str(args.port),
    }
    
    if args.mode == "minimal":
        # Minimal konfiguration - inaktivera tjänster som kräver mycket resurser
        env_vars["DISABLE_WEBSOCKET"] = "true"
        env_vars["DISABLE_NONCE_MANAGER"] = "true"
        env_vars["MOCK_EXCHANGE_SERVICE"] = "true"
        print("🔧 Minimal konfiguration: WebSockets och GlobalNonceManager inaktiverade")
        
    elif args.mode == "api":
        # API-fokuserat läge - inaktivera bara WebSockets
        env_vars["DISABLE_WEBSOCKET"] = "true"
        env_vars["MOCK_EXCHANGE_SERVICE"] = "true"
        print("🔧 API-läge: WebSockets inaktiverade, GlobalNonceManager aktiverad")
        
    elif args.mode == "websocket":
        # WebSocket-fokuserat läge
        env_vars["MOCK_EXCHANGE_SERVICE"] = "true"
        print("🔧 WebSocket-läge: WebSockets aktiverade, GlobalNonceManager aktiverad")
        
    else:  # full mode
        print("🔧 Fullständigt läge: Alla tjänster aktiverade")
    
    # Skapa .env-fil för development
    env_file = create_env_file(env_vars)
    
    # Sätt upp kommando för att starta FastAPI
    cd_cmd = "cd " + project_root
    env_cmd = f"set DOTENV_PATH={env_file}" if is_powershell() else f"export DOTENV_PATH={env_file}"
    
    uvicorn_options = []
    if not args.no_reload:
        uvicorn_options.append("--reload")
    
    if is_powershell():
        python_cmd = (
            f"python -c \"import sys; "
            f"sys.path.append('{project_root}'); "
            f"from dotenv import load_dotenv; "
            f"load_dotenv('{env_file}'); "
            f"import uvicorn; "
            f"uvicorn.run('backend.fastapi_app:app', host='0.0.0.0', port={args.port}, {'' if args.no_reload else 'reload=True'})\""
        )
        run_command([cd_cmd, env_cmd, python_cmd])
    else:
        python_cmd = f"cd {project_root} && python -m backend.fastapi_app"
        run_command(f"{env_cmd} && {python_cmd}")


if __name__ == "__main__":
    main() 