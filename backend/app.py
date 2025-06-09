from flask import Flask
from flask_cors import CORS
import os
import importlib.util

"""
backend/app.py

Flask application entrypoint that dynamically registers all API routes.
"""
import os
import sys
import logging
import importlib.util

from flask import Flask
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def register_routes():
    """
    Dynamically load and register all route modules under backend/routes.
    """
    routes_path = os.path.join(os.path.dirname(__file__), 'routes')
    for filename in os.listdir(routes_path):
        if not filename.endswith('.py') or filename.startswith('__'):
            continue

        module_basename = filename[:-3]
        module_name = f"backend.routes.{module_basename}"
        file_path = os.path.join(routes_path, filename)
        logger.info("Loading route: %s", module_name)

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Ensure module is in sys.modules for proper imports and patching
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                logger.info("Registering route: %s", module_name)
                module.register(app)
            else:
                logger.warning("No 'register(app)' in %s", module_name)
        else:
            logger.error("Failed to load spec/loader for %s", module_name)

register_routes()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
