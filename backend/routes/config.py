from flask import request, jsonify
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

def register(app):
    @app.route('/api/config', methods=['GET'])
    def get_config():
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return jsonify(config)

    @app.route('/api/config', methods=['POST'])
    def update_config():
        data = request.get_json()
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"message": "Config updated successfully"})
