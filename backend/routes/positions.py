from flask import jsonify
from services.positions_service import get_mock_positions

def register(app):
    @app.route('/api/positions', methods=['GET'])
    def get_positions():
        """
        Hämta nuvarande positioner (mockad data).
        ---
        responses:
            200:
                description: Lista med positioner
        """
        return jsonify(get_mock_positions())
