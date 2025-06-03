from flask import Blueprint, jsonify
from services.status_service import get_status

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
        return jsonify(get_status())
