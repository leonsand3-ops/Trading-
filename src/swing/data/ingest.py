"""Fetch bars from a provider and append them to the store."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime

import polars as pl

from swing.data.calendar import session_close_utc
from swing.data.instruments import InstrumentRegistry
from swing.data.providers.base import BarProvider, ProviderError
from swing.data.schema import UTC_DATETIME
from swing.data.store import DataStore


@dataclass
class IngestResult:
    rows_written: dict[str, int] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)


def ingest_bars(
    provider: BarProvider,
    symbols: Sequence[str],
    start: date,
    end: date,
    store: DataStore,
    now: datetime,
    on_symbol: Callable[[int, int, str], None] | None = None,
) -> IngestResult:
    """Download ``symbols`` and store them as a new version stamped ``now``.

    Bars whose session has not closed yet at ``now`` are dropped, so an intraday
    snapshot is never stored as if it were a finished daily bar. ``on_symbol`` is called
    with (position, total, symbol) before each download, for progress output.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    registry = InstrumentRegistry(store)
    result = IngestResult()
    for position, symbol in enumerate(symbols, start=1):
        symbol = symbol.strip().upper()
        if on_symbol is not None:
            on_symbol(position, len(symbols), symbol)
        try:
            raw = provider.fetch_daily_bars(symbol, start, end)
        except ProviderError as exc:
            result.failures[symbol] = str(exc)
            continue
        raw = raw.unique(subset=["date"], keep="last").sort("date")
        known_at = [session_close_utc(d) for d in raw.get_column("date").to_list()]
        bars = raw.with_columns(
            pl.Series("known_at", known_at, dtype=UTC_DATETIME),
        ).filter(pl.col("known_at") <= now)
        if bars.is_empty():
            result.failures[symbol] = "no completed sessions in range"
            continue
        instrument_id = registry.resolve(provider.source, symbol, now)
        bars = bars.with_columns(
            pl.lit(instrument_id).alias("instrument_id"),
            pl.lit(provider.adjustment).alias("adjustment"),
            pl.lit(provider.source).alias("source"),
            pl.lit(now).cast(UTC_DATETIME).alias("ingested_at"),
        )
        store.bars.append(bars, now)
        result.rows_written[symbol] = bars.height
    return result
