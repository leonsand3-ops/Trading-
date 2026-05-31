import pandas as pd
import ta
import yfinance as yf
from typing import Dict, Optional

TIMEFRAME_MAP = {
    "15min": ("1d", "15m"),
    "day": ("60d", "1d"),
    "swing": ("180d", "1d"),
}


def fetch_ohlcv(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    period, interval = TIMEFRAME_MAP.get(timeframe, ("60d", "1d"))
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception:
        return None


def compute_indicators(df: pd.DataFrame) -> Dict:
    if df is None or len(df) < 30:
        return {}

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Trend
    ema9 = ta.trend.ema_indicator(close, window=9)
    ema21 = ta.trend.ema_indicator(close, window=21)
    ema50 = ta.trend.ema_indicator(close, window=50)

    # Momentum
    rsi = ta.momentum.rsi(close, window=14)
    macd = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)

    # Volatility
    bb = ta.volatility.BollingerBands(close, window=20)
    atr = ta.volatility.average_true_range(high, low, close, window=14)

    # Volume
    obv = ta.volume.on_balance_volume(close, volume)

    last = -1
    return {
        "price": round(float(close.iloc[last]), 4),
        "ema9": _safe(ema9, last),
        "ema21": _safe(ema21, last),
        "ema50": _safe(ema50, last),
        "rsi": _safe(rsi, last),
        "macd": _safe(macd.macd(), last),
        "macd_signal": _safe(macd.macd_signal(), last),
        "macd_hist": _safe(macd.macd_diff(), last),
        "bb_upper": _safe(bb.bollinger_hband(), last),
        "bb_mid": _safe(bb.bollinger_mavg(), last),
        "bb_lower": _safe(bb.bollinger_lband(), last),
        "atr": _safe(atr, last),
        "obv_trend": _obv_trend(obv),
        "prev_close": round(float(close.iloc[-2]), 4) if len(close) >= 2 else None,
        "high_5": round(float(high.iloc[-5:].max()), 4),
        "low_5": round(float(low.iloc[-5:].min()), 4),
    }


def _safe(series, idx):
    try:
        val = float(series.iloc[idx])
        return round(val, 4) if not pd.isna(val) else None
    except Exception:
        return None


def _obv_trend(obv):
    try:
        if obv is None or len(obv) < 5:
            return "neutral"
        recent = obv.iloc[-5:].values
        return "rising" if recent[-1] > recent[0] else "falling"
    except Exception:
        return "neutral"
