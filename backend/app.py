from flask import Flask
from flask_cors import CORS
import os
import importlib.util

app = Flask(__name__)
CORS(app)

# Dynamiskt ladda alla routes i ./routes/
def register_routes():
    routes_path = os.path.join(os.path.dirname(__file__), 'routes')
    for filename in os.listdir(routes_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            file_path = os.path.join(routes_path, filename)
            print(f"📦 Loading route: {module_name}...")
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                print(f"✅ Registering route: {module_name}")
                module.register(app)
            else:
                print(f"⚠️  No 'register(app)' in {module_name}")

register_routes()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
