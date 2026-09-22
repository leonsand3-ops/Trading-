"""Provider interface. Every data vendor is wrapped behind this protocol."""

from datetime import date
from typing import Protocol

import polars as pl


class ProviderError(RuntimeError):
    """A provider could not deliver data for a request."""


class BarProvider(Protocol):
    source: str
    """Short, stable name stored with every row, e.g. ``"yahoo"``."""

    adjustment: str
    """How prices are adjusted, e.g. ``"split"`` or ``"none"``."""

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> pl.DataFrame:
        """Daily bars from ``start`` to ``end`` inclusive, in ``RAW_BAR_SCHEMA``."""
        ...
