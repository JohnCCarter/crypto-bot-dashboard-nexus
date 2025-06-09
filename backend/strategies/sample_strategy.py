"""Sample trading strategy interface implementation."""

import pandas as pd
from typing import NamedTuple


class TradeSignal(NamedTuple):
    """
    Represents a trading signal result.
    Attributes:
        action: 'buy', 'sell', or 'hold'
        confidence: Confidence level between 0.0 and 1.0.
    """
    action: str
    confidence: float


def run_strategy(data: pd.DataFrame) -> TradeSignal:
    """
    Run the trading strategy logic on input price DataFrame.

    :param data: Historical price/time data as pandas DataFrame.
    :return: A TradeSignal indicating the recommended action.
    """
    # TODO: Implement strategy logic. This stub always issues 'hold'.
    return TradeSignal(action='hold', confidence=0.0)