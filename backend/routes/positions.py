from flask import jsonify
from backend.services.positions_service import get_mock_positions

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
        try:
            data = get_mock_positions()
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
