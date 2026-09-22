from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from swing.data.providers.base import ProviderError
from swing.data.schema import RAW_BAR_SCHEMA
from swing.data.store import DataStore


def weekdays(start: date, n: int) -> list[date]:
    days: list[date] = []
    d = start
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def make_raw_bars(
    start: date, n: int, first_close: float = 100.0, step: float = 1.0
) -> pl.DataFrame:
    """Clean synthetic bars: close rises by ``step`` each weekday."""
    days = weekdays(start, n)
    closes = [first_close + i * step for i in range(n)]
    return pl.DataFrame(
        {
            "date": days,
            "open": [c - 0.5 for c in closes],
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1_000_000.0] * n,
        },
        schema=RAW_BAR_SCHEMA,
    )


class FakeProvider:
    source = "fake"
    adjustment = "split"

    def __init__(self, data: dict[str, pl.DataFrame]) -> None:
        self.data = data

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> pl.DataFrame:
        if symbol not in self.data:
            raise ProviderError(f"unknown symbol {symbol}")
        return self.data[symbol].filter(pl.col("date").is_between(start, end))


@pytest.fixture
def store(tmp_path: Path) -> DataStore:
    return DataStore(tmp_path / "lake")
