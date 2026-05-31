from typing import Dict
from ..core.config import settings


def validate_and_size(signal: Dict, account_size: float = None) -> Dict:
    if account_size is None:
        account_size = settings.default_account_size
    signal = dict(signal)
    if signal.get("signal") == "HOLD":
        signal["position_size"] = 0
        signal["risk_amount"] = 0
        signal["risk_reward"] = None
        return signal
    price = signal.get("price", 0)
    sl = signal.get("stop_loss")
    tp = signal.get("take_profit")
    if not price or not sl:
        signal["signal"] = "HOLD"; signal["position_size"] = 0; signal["risk_amount"] = 0
        return signal
    risk_per_share = abs(price - sl)
    if risk_per_share == 0:
        signal["signal"] = "HOLD"; signal["position_size"] = 0
        return signal
    max_risk = account_size * (settings.max_risk_per_trade_pct / 100)
    quantity = max_risk / risk_per_share
    max_notional = account_size * 0.20
    if quantity * price > max_notional:
        quantity = max_notional / price
    rr = None
    if tp:
        reward = abs(tp - price)
        rr = round(reward / risk_per_share, 2)
        if rr < 1.3:
            signal["signal"] = "HOLD"; signal["position_size"] = 0
            signal["risk_reward"] = rr
            signal["reasoning"] = f"Signal rejected: R/R {rr} < 1.3 minimum."
            return signal
    signal["position_size"] = round(quantity, 4)
    signal["risk_amount"] = round(max_risk, 2)
    signal["risk_reward"] = rr
    signal["account_size"] = account_size
    return signal
