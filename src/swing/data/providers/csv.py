"""Import daily bars from CSV files, one ``<SYMBOL>.csv`` per instrument.

Expected columns (case-insensitive): ``date, open, high, low, close, volume``.
Useful for vendor exports (for example from Norgate on Windows) and manual data.
"""

from datetime import date
from pathlib import Path

import polars as pl

from swing.data.providers.base import ProviderError
from swing.data.schema import RAW_BAR_SCHEMA, SchemaError, conform


class CsvProvider:
    def __init__(self, directory: Path, source: str = "csv", adjustment: str = "split") -> None:
        self.directory = directory
        self.source = source
        self.adjustment = adjustment

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> pl.DataFrame:
        path = self.directory / f"{symbol.upper()}.csv"
        if not path.exists():
            raise ProviderError(f"{path} not found")
        df = pl.read_csv(path, try_parse_dates=True)
        df = df.rename({c: c.strip().lower() for c in df.columns})
        try:
            df = conform(df, RAW_BAR_SCHEMA)
        except SchemaError as exc:
            raise ProviderError(f"{path}: {exc}") from exc
        return df.filter(pl.col("date").is_between(start, end)).sort("date")
