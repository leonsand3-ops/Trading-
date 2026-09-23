"""Fetch bars from a provider and append them to the store."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import polars as pl

from swing.data.calendar import session_close_utc
from swing.data.instruments import InstrumentRegistry
from swing.data.providers.base import BarProvider, ProviderError
from swing.data.schema import UTC_DATETIME
from swing.data.store import DataStore

# Bars are only stored once this long after the close, so prints from the closing
# auction have been included by the vendor.
SETTLE_DELAY = timedelta(hours=1)
# Incremental updates re-download this many days before the last stored bar, so late
# vendor corrections replace earlier versions.
INCREMENTAL_OVERLAP = timedelta(days=10)


@dataclass
class IngestResult:
    rows_written: dict[str, int] = field(default_factory=dict)
    last_date: dict[str, date] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)


def ingest_bars(
    provider: BarProvider,
    symbols: Sequence[str],
    start: date | Mapping[str, date],
    end: date,
    store: DataStore,
    now: datetime,
    on_symbol: Callable[[int, int, str], None] | None = None,
) -> IngestResult:
    """Download ``symbols`` and store them as a new version stamped ``now``.

    Bars whose session closed less than ``SETTLE_DELAY`` before ``now`` are dropped, so
    an intraday snapshot or a not yet corrected bar is never stored as a finished daily
    bar. ``start`` is either one date for all symbols or a date per symbol.
    ``on_symbol`` is called with (position, total, symbol) before each download.
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
            symbol_start = start if isinstance(start, date) else start[symbol]
            raw = provider.fetch_daily_bars(symbol, symbol_start, end)
        except ProviderError as exc:
            result.failures[symbol] = str(exc)
            continue
        raw = raw.unique(subset=["date"], keep="last").sort("date")
        known_at = [session_close_utc(d) for d in raw.get_column("date").to_list()]
        bars = raw.with_columns(
            pl.Series("known_at", known_at, dtype=UTC_DATETIME),
        ).filter(pl.col("known_at") <= now - SETTLE_DELAY)
        if bars.is_empty():
            result.failures[symbol] = "no settled sessions in range"
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
        result.last_date[symbol] = bars.get_column("date").max()  # type: ignore[assignment]
    return result


def incremental_starts(
    store: DataStore, source: str, symbols: Sequence[str], default_start: date
) -> dict[str, date]:
    """Start date per symbol: shortly before its last stored bar, or ``default_start``."""
    registry = InstrumentRegistry(store)
    last_dates = {
        row["instrument_id"]: row["date"]
        for row in store.latest_bars()
        .group_by("instrument_id")
        .agg(pl.col("date").max())
        .iter_rows(named=True)
    }
    starts = {}
    for symbol in symbols:
        symbol = symbol.strip().upper()
        instrument_id = registry.lookup(source, symbol)
        last = last_dates.get(instrument_id) if instrument_id else None
        starts[symbol] = last - INCREMENTAL_OVERLAP if last else default_start
    return starts
