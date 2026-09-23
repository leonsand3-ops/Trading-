"""Yahoo Finance via ``yfinance``. For development only.

Unofficial, occasionally breaks, and has no delisted symbols, so any backtest on this
data carries survivorship bias. Install with ``uv sync --extra yahoo``.
Prices are split-adjusted but not dividend-adjusted (``auto_adjust=False``).

Yahoo's open sometimes comes from a different feed than its high and low, so the open
can sit slightly outside the day's range (seen on DIA, GS, UNH and DIS for 2026-09-22,
unchanged a day later). Such small gaps are repaired by widening high/low; larger ones
are left alone so the quality checks flag them.
"""

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta

import polars as pl

from swing.data.providers.base import ProviderError
from swing.data.schema import RAW_BAR_SCHEMA

# Largest open/close excursion outside high/low, as a share of close, that is repaired.
MAX_RANGE_REPAIR = 0.01


def repair_range(df: pl.DataFrame) -> pl.DataFrame:
    """Widen high/low to include open and close when they miss by a small amount."""
    top = pl.max_horizontal("open", "close")
    bottom = pl.min_horizontal("open", "close")
    small = MAX_RANGE_REPAIR * pl.col("close")
    return df.with_columns(
        pl.when((pl.col("high") < top) & (top - pl.col("high") <= small))
        .then(top)
        .otherwise(pl.col("high"))
        .alias("high"),
        pl.when((pl.col("low") > bottom) & (pl.col("low") - bottom <= small))
        .then(bottom)
        .otherwise(pl.col("low"))
        .alias("low"),
    )


def normalize_yahoo(
    index: Sequence[datetime | date],
    columns: Mapping[str, Sequence[float]],
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
    df = df.drop_nulls().filter(pl.col("close").is_not_nan()).sort("date")
    return repair_range(df)


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
