def get_mock_orderbook(symbol):
    """
    Returnerar en mockad orderbok för given symbol.
    :param symbol: str
    :return: dict med bids och asks
    """
    return {
        "bids": [[27800.5, 1.2], [27795.0, 0.6], [27790.0, 0.8]],
        "asks": [[27810.0, 0.8], [27815.5, 1.0], [27820.0, 0.5]],
    }
