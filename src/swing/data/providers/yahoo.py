"""Yahoo Finance via ``yfinance``. For development only.

Unofficial, occasionally breaks, and has no delisted symbols, so any backtest on this
data carries survivorship bias. Install with ``uv sync --extra yahoo``.
Prices are split-adjusted but not dividend-adjusted (``auto_adjust=False``).
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta

import polars as pl

from swing.data.providers.base import ProviderError
from swing.data.schema import RAW_BAR_SCHEMA


def normalize_yahoo(
    index: Sequence[datetime | date],
    columns: dict[str, Sequence[float]],
) -> pl.DataFrame:
    """Convert yfinance ``history()`` output to ``RAW_BAR_SCHEMA``."""
    dates = [d.date() if isinstance(d, datetime) else d for d in index]
    df = pl.DataFrame(
        {
            "date": dates,
            "open": list(columns["Open"]),
            "high": list(columns["High"]),
            "low": list(columns["Low"]),
            "close": list(columns["Close"]),
            "volume": list(columns["Volume"]),
        },
        schema=RAW_BAR_SCHEMA,
    )
    return df.drop_nulls().filter(pl.col("close").is_not_nan()).sort("date")


class YahooProvider:
    source = "yahoo"
    adjustment = "split"

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> pl.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError("yfinance is not installed: run `uv sync --extra yahoo`") from exc

        try:
            hist = yf.Ticker(symbol).history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),  # yfinance end is exclusive
                interval="1d",
                auto_adjust=False,
                actions=False,
                raise_errors=True,
            )
        except Exception as exc:  # yfinance raises many unrelated exception types
            raise ProviderError(f"{symbol}: {exc}") from exc
        if hist is None or hist.empty:
            raise ProviderError(f"no data for {symbol}")
        columns = {name: hist[name].tolist() for name in ("Open", "High", "Low", "Close", "Volume")}
        return normalize_yahoo([ts.to_pydatetime() for ts in hist.index], columns)
