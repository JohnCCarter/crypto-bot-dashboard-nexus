#!/usr/bin/env python3
"""
Copilot Helper - Förbättra integrationen med GitHub Copilot
Används för att generera Copilot kontext och förbättra kodförslagen
"""
import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
STRATEGIES_DIR = PROJECT_ROOT / "backend" / "strategies"
SERVICES_DIR = PROJECT_ROOT / "backend" / "services"
COMPONENTS_DIR = PROJECT_ROOT / "src" / "components"

def generate_strategy_context() -> Dict[str, Any]:
    """Generera kontext för strategifiler som hjälper Copilot förstå projektstrukturen."""
    strategies = []
    indicators = {}
    
    # Samla in strategier
    for file in STRATEGIES_DIR.glob("*.py"):
        if file.name == "__init__.py" or file.name == "indicators.py":
            continue
        strategies.append(file.stem)
    
    # Samla in indikatorer
    indicators_file = STRATEGIES_DIR / "indicators.py"
    if indicators_file.exists():
        with open(indicators_file, "r") as f:
            content = f.read()
            # Enkel parsing av funktionsdefinitioner
            funcs = re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", content)
            indicators = {name: args for name, args in funcs}
    
    return {
        "strategies": strategies,
        "indicators": indicators
    }

def generate_service_context() -> Dict[str, Any]:
    """Generera kontext för servicefiler."""
    services = []
    
    for file in SERVICES_DIR.glob("*.py"):
        if file.name == "__init__.py":
            continue
        services.append(file.stem)
    
    return {
        "services": services
    }

def generate_component_context() -> Dict[str, Any]:
    """Generera kontext för React komponenter."""
    components = []
    
    for file in COMPONENTS_DIR.glob("*.tsx"):
        components.append(file.stem)
    
    return {
        "components": components
    }

def update_copilot_context():
    """Uppdatera Copilot kontext baserat på aktuell kodstruktur."""
    context_dir = PROJECT_ROOT / ".github" / "copilot"
    context_dir.mkdir(exist_ok=True, parents=True)
    
    # Generera och spara olika kontexter
    contexts = {
        "strategy_context.json": generate_strategy_context(),
        "service_context.json": generate_service_context(),
        "component_context.json": generate_component_context(),
    }
    
    for filename, context in contexts.items():
        with open(context_dir / filename, "w") as f:
            json.dump(context, f, indent=2)
    
    print(f"Uppdaterat Copilot-kontexter i {context_dir}")

def main():
    """Huvudfunktion för Copilot-hjälparen."""
    parser = argparse.ArgumentParser(
        description="Hjälpverktyg för GitHub Copilot integration"
    )
    parser.add_argument(
        "--update-context", 
        action="store_true", 
        help="Uppdatera Copilot kontext"
    )
    
    args = parser.parse_args()
    
    if args.update_context:
        update_copilot_context()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 