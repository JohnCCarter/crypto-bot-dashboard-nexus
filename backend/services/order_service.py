import datetime

order_log = []

def place_order(data):
    """
    Skapar och loggar en order baserat på indata.
    :param data: dict med orderparametrar (symbol, order_type, side, amount, price)
    :return: dict med orderinfo
    """
    order = {
        "symbol": data.get("symbol"),
        "order_type": data.get("order_type"),
        "side": data.get("side"),
        "amount": data.get("amount"),
        "price": data.get("price"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    order_log.append(order)
    return order 