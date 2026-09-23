"""Column schemas for stored market data.

Every stored bar carries two timestamps:

* ``known_at`` - when the information became available in the world. For a daily bar
  this is the regular session close of that date (16:00 New York time). This is the
  timestamp as-of access filters on.
* ``ingested_at`` - when this system stored the row. Rows are never overwritten; a
  re-download is a new version and the latest ``ingested_at`` wins.
"""

import polars as pl

from swing.data.calendar import NEW_YORK

UTC_DATETIME = pl.Datetime(time_unit="us", time_zone="UTC")

# Bars as returned by a provider, before they are tied to an instrument.
RAW_BAR_SCHEMA: dict[str, pl.DataType] = {
    "date": pl.Date(),
    "open": pl.Float64(),
    "high": pl.Float64(),
    "low": pl.Float64(),
    "close": pl.Float64(),
    "volume": pl.Float64(),
}

BAR_SCHEMA: dict[str, pl.DataType] = {
    "instrument_id": pl.String(),
    **RAW_BAR_SCHEMA,
    "adjustment": pl.String(),
    "source": pl.String(),
    "known_at": UTC_DATETIME,
    "ingested_at": UTC_DATETIME,
}

INSTRUMENT_SCHEMA: dict[str, pl.DataType] = {
    "instrument_id": pl.String(),
    "source": pl.String(),
    "symbol": pl.String(),
    "ingested_at": UTC_DATETIME,
}

BAR_KEY = ["instrument_id", "date"]

# A stored bar version is final only if it was ingested on a later New York calendar
# date than the bar itself. On the evening of a session Yahoo serves a provisional bar
# built from live quotes and drops it again overnight: the 2026-09-22 bars fetched at
# 17:43 New York time had open above high for four symbols, and the next morning Yahoo
# returned no 2026-09-22 bar at all. Non-final versions are never stored or read.
FINAL_BAR = pl.col("ingested_at").dt.convert_time_zone(NEW_YORK.key).dt.date() > pl.col("date")


class SchemaError(ValueError):
    """Raised when a frame does not match the expected schema."""


def conform(df: pl.DataFrame, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    """Select and cast ``df`` to ``schema``, failing loudly on missing columns."""
    missing = [name for name in schema if name not in df.columns]
    if missing:
        raise SchemaError(f"missing columns: {missing}")
    try:
        return df.select([pl.col(name).cast(dtype, strict=True) for name, dtype in schema.items()])
    except pl.exceptions.PolarsError as exc:
        raise SchemaError(str(exc)) from exc
