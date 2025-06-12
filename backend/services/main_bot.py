from dotenv import load_dotenv
import traceback
import os

from backend.services.config_service import Config
from backend.strategies.ema_crossover_strategy import run_strategy as run_ema
from backend.strategies.rsi_strategy import run_strategy as run_rsi
from backend.strategies.fvg_strategy import run_strategy as run_fvg
from backend.services.risk_manager import RiskManager, RiskParameters
from backend.services.trading_window import TradingWindow
from backend.services.notifications import Notifier

load_dotenv()

email = os.getenv("EMAIL_ADDRESS")
password = os.getenv("SMTP_PASSWORD")


def main():
    config = Config.load()
    # Strategiparametrar
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")
    
    ema_params = config.get("strategy", {}).copy()
    rsi_params = config.get("strategy", {}).copy()
    fvg_params = config.get("fvg_strategy", {}).copy()
    symbol = config.get("strategy", {}).get("symbol")
    timeframe = config.get("strategy", {}).get("timeframe")
    for params in (ema_params, rsi_params, fvg_params):
        params["symbol"] = symbol
        params["timeframe"] = timeframe

    # Riskparametrar
    risk_conf = config.get("risk", {})
    if not isinstance(risk_conf, dict):
        raise ValueError("Risk configuration must be a dictionary")
    
    risk_params = RiskParameters(
        max_position_size=risk_conf["risk_per_trade"],
        max_leverage=1,  # Lägg till i config vid behov
        stop_loss_pct=risk_conf["stop_loss_percent"] / 100,
        take_profit_pct=risk_conf["take_profit_percent"] / 100,
        max_daily_loss=risk_conf["max_daily_loss"] / 100,
        max_open_positions=5  # Lägg till i config vid behov
    )
    risk_manager = RiskManager(risk_params)

    # Trading window
    trading_window = TradingWindow(config.get("trading_window", {}))
    # Notifications
    notif_conf = config.get("notifications", {})
    if not isinstance(notif_conf, dict):
        raise ValueError("Notifications configuration must be a dictionary")
    
    notifier = Notifier(
        smtp_server=notif_conf.get("smtp_server", "smtp.example.com"),
        smtp_port=notif_conf.get("smtp_port", 465),
        sender=notif_conf.get("sender", email),
        receiver=notif_conf["receiver"]
    )

    # Exempel på användning:
    if trading_window.is_within_window() and trading_window.can_trade():
        # Hämta market data här (mockat exempel):
        import pandas as pd
        data = pd.DataFrame({
            "open": [
                100, 102, 101, 105, 110, 108, 112, 115, 117, 120, 119, 121,
                123, 125, 127, 126, 128, 130, 129, 131, 133, 135, 134, 136,
                138, 140
            ],
            "high": [
                103, 104, 103, 108, 112, 110, 115, 118, 120, 123, 122, 124,
                126, 128, 130, 129, 131, 133, 132, 134, 136, 138, 137, 139,
                141, 143
            ],
            "low": [
                99, 101, 100, 104, 109, 107, 111, 114, 116, 119, 118, 120,
                122, 124, 126, 125, 127, 129, 128, 130, 132, 134, 133, 135,
                137, 139
            ],
            "close": [
                102, 103, 102, 107, 111, 109, 114, 117, 119, 122, 121, 123,
                125, 127, 129, 128, 130, 132, 131, 133, 135, 137, 136, 138,
                140, 142
            ]
        })
        ema_signal = run_ema(data, ema_params)
        rsi_signal = run_rsi(data, rsi_params)
        fvg_signal = run_fvg(data, fvg_params)
        # Exempel: riskhantering
        portfolio_value = 10000
        current_positions = {}
        position_size = risk_manager.calculate_position_size(
            ema_signal.confidence, portfolio_value, current_positions
        )
        print(f"EMA-signal: {ema_signal}")
        print(f"RSI-signal: {rsi_signal}")
        print(f"FVG-signal: {fvg_signal}")
        print(f"Position size (EMA): {position_size}")
        trading_window.register_trade()
        notifier.send(f"Trade utförd: {ema_signal.action} {position_size}")
    else:
        notifier.send("Utanför trading window eller max trades uppnått.")
    if __name__ == "__main__":
        try:
            main()
        except Exception:
            traceback.print_exc()