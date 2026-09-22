"""Stable instrument identifiers.

Tickers change and get reused, so everything downstream refers to an
``instrument_id``. The registry maps a provider's symbol to that id and persists the
mapping, so the same symbol from the same source always resolves to the same id.
"""

import uuid
from datetime import datetime

import polars as pl

from swing.data.store import DataStore


def new_instrument_id() -> str:
    return f"ins_{uuid.uuid4().hex[:12]}"


class InstrumentRegistry:
    def __init__(self, store: DataStore) -> None:
        self._store = store
        latest = store.instruments.read_latest(["source", "symbol"])
        self._ids: dict[tuple[str, str], str] = {
            (row["source"], row["symbol"]): row["instrument_id"]
            for row in latest.iter_rows(named=True)
        }

    def lookup(self, source: str, symbol: str) -> str | None:
        return self._ids.get((source, symbol.upper()))

    def resolve(self, source: str, symbol: str, ingested_at: datetime) -> str:
        """Return the id for ``symbol``, registering it if it is new."""
        symbol = symbol.upper()
        existing = self.lookup(source, symbol)
        if existing is not None:
            return existing
        instrument_id = new_instrument_id()
        self._store.instruments.append(
            pl.DataFrame(
                {
                    "instrument_id": [instrument_id],
                    "source": [source],
                    "symbol": [symbol],
                    "ingested_at": [ingested_at],
                }
            ),
            ingested_at,
        )
        self._ids[(source, symbol)] = instrument_id
        return instrument_id

    def symbols(self) -> dict[str, str]:
        """Map of instrument_id to symbol."""
        return {instrument_id: symbol for (_, symbol), instrument_id in self._ids.items()}
