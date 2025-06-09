from flask import Blueprint, jsonify
from backend.services.status_service import get_status

def register(app):
    @app.route('/api/status', methods=['GET'])
    def get_status_route():
        """
        Hämta API-status och mockad balans.
        ---
        responses:
            200:
                description: Status och balans
        """
        try:
            data = get_status()
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
