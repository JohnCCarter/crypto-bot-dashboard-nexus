import pytest
from unittest.mock import patch
from backend.services.exchange import ExchangeService


@pytest.fixture
def exchange_service_mock():
    """
    Provides a mocked ExchangeService instance where time.time() is patched
    to ensure the nonce always increments, preventing 'Nonce is too small' errors.
    """
    with patch("time.time") as mock_time:
        # Start with a realistic timestamp and increment it on each call
        mock_time.side_effect = (
            i for i in range(int(1700000000), int(1700000000) + 1000)
        )

        # Provide dummy credentials as they are required by the constructor
        service = ExchangeService(
            exchange_id="bitfinex", api_key="test_key", api_secret="test_secret"
        )
        yield service
