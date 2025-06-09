"""RSI strategy stub implementation."""

import pandas as pd
from backend.strategies.sample_strategy import TradeSignal


def run_strategy(data: pd.DataFrame) -> TradeSignal:
    """
    Placeholder for RSI strategy.

    :param data: Historical price/time data as pandas DataFrame.
    :return: A TradeSignal indicating the recommended action.
    """
    # TODO: Implement RSI logic. This stub always issues 'hold'.
    return TradeSignal(action='hold', confidence=0.0)