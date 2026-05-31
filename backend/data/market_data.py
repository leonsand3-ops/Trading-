import pandas as pd
import pandas_ta as ta
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
    ema9 = ta.ema(close, length=9)
    ema21 = ta.ema(close, length=21)
    ema50 = ta.ema(close, length=50)
    rsi = ta.rsi(close, length=14)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    bb = ta.bbands(close, length=20)
    atr = ta.atr(high, low, close, length=14)
    obv = ta.obv(close, volume)
    last = -1
    return {
        "price": round(float(close.iloc[last]), 4),
        "ema9": _safe(ema9, last),
        "ema21": _safe(ema21, last),
        "ema50": _safe(ema50, last),
        "rsi": _safe(rsi, last),
        "macd": _safe(macd_df["MACD_12_26_9"] if macd_df is not None else None, last),
        "macd_signal": _safe(macd_df["MACDs_12_26_9"] if macd_df is not None else None, last),
        "macd_hist": _safe(macd_df["MACDh_12_26_9"] if macd_df is not None else None, last),
        "bb_upper": _safe(bb["BBU_20_2.0"] if bb is not None else None, last),
        "bb_mid": _safe(bb["BBM_20_2.0"] if bb is not None else None, last),
        "bb_lower": _safe(bb["BBL_20_2.0"] if bb is not None else None, last),
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
