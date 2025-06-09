def get_mock_positions():
    """
    Returnerar en lista med mockade positioner.
    :return: list av dicts
    """
    return [
        {
            "symbol": "BTC/USD",
            "amount": 0.1,
            "entry_price": 27000.0,
            "pnl": 320.0,
            "timestamp": "2025-05-26T08:30:00Z",
        },
        {
            "symbol": "ETH/USD",
            "amount": 2.0,
            "entry_price": 1800.0,
            "pnl": -45.0,
            "timestamp": "2025-05-26T07:45:00Z",
        },
    ]
