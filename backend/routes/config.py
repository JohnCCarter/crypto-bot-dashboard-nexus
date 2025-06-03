from flask import request, jsonify
from services.config_service import get_config, update_config

def register(app):
    @app.route('/api/config', methods=['GET'])
    def get_config_route():
        """
        Hämta nuvarande konfiguration.
        ---
        responses:
            200:
                description: Nuvarande konfiguration
        """
        config = get_config()
        return jsonify(config)

    @app.route('/api/config', methods=['POST'])
    def update_config_route():
        """
        Uppdatera konfigurationen.
        ---
        requestBody:
            description: Ny konfigurationsdata
        responses:
            200:
                description: Konfiguration uppdaterad
            400:
                description: Felaktig indata
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        update_config(data)
        return jsonify({"message": "Config updated successfully"})
