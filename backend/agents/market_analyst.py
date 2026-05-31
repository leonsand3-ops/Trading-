from typing import Optional, Dict
from ..data.market_data import fetch_ohlcv, compute_indicators


def analyze_market(symbol: str, timeframe: str) -> Optional[Dict]:
    df = fetch_ohlcv(symbol, timeframe)
    if df is None:
        return None
    indicators = compute_indicators(df)
    if not indicators:
        return None
    return {"symbol": symbol, "timeframe": timeframe, "indicators": indicators}
