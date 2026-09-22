"""As-of access: the only way decision code may read market data.

An ``AsOfView`` exposes exactly the rows whose ``known_at`` is at or before its
``as_of`` timestamp. Feature, setup and risk code receive a view and never the full
history, so they cannot see the future by construction.

Version resolution (latest ``ingested_at`` per bar) happens once, before as-of
filtering. A later re-download that corrects history is therefore used for all
dates; that is a deliberate trade-off for split-adjusted vendor data.
"""

from datetime import date, datetime

import polars as pl

from swing.data.calendar import session_close_utc
from swing.data.schema import BAR_KEY
from swing.data.store import DataStore


class BarHistory:
    """All resolved bars in memory, sorted by instrument and date."""

    def __init__(self, bars: pl.DataFrame) -> None:
        self._bars = bars.sort(BAR_KEY)

    @classmethod
    def load(cls, store: DataStore) -> "BarHistory":
        return cls(store.latest_bars())

    def as_of(self, when: datetime) -> "AsOfView":
        if when.tzinfo is None:
            raise ValueError("as_of timestamp must be timezone-aware")
        return AsOfView(self._bars.filter(pl.col("known_at") <= when), when)

    def at_close(self, day: date) -> "AsOfView":
        """View as of the regular session close of ``day``."""
        return self.as_of(session_close_utc(day))


class AsOfView:
    def __init__(self, bars: pl.DataFrame, as_of: datetime) -> None:
        self._bars = bars
        self.as_of = as_of

    def bars(self, instrument_id: str, lookback: int | None = None) -> pl.DataFrame:
        """Bars for one instrument, oldest first, optionally only the last ``lookback``."""
        df = self._bars.filter(pl.col("instrument_id") == instrument_id)
        return df.tail(lookback) if lookback is not None else df

    def all_bars(self) -> pl.DataFrame:
        return self._bars

    def instrument_ids(self) -> list[str]:
        return self._bars.get_column("instrument_id").unique().sort().to_list()
