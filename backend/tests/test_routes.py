import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
from unittest.mock import patch

from backend.app import app


def test_status_endpoint():
    client = app.test_client()
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('status') == 'running'
    assert 'balance' in data


@patch('balances.fetch_balances')
def test_balances_endpoint(mock_fetch_balances):
    mock_fetch_balances.return_value = {
        'total': {'USD': 100.0, 'BTC': 0.1},
        'free': {'USD': 80.0, 'BTC': 0.05}
    }
    client = app.test_client()
    response = client.get('/api/balances')
    assert response.status_code == 200
    expected = [
        {'currency': 'USD', 'total_balance': 100.0, 'available': 80.0},
        {'currency': 'BTC', 'total_balance': 0.1, 'available': 0.05}
    ]
    assert response.get_json() == expected

