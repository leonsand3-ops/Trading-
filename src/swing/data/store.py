"""Append-only Parquet storage.

Each write creates a new part file; nothing is ever modified or deleted. Readers
resolve versions by keeping the row with the latest ``ingested_at`` per key.
"""

import uuid
from datetime import datetime
from pathlib import Path

import polars as pl

from swing.data.schema import BAR_KEY, BAR_SCHEMA, FINAL_BAR, INSTRUMENT_SCHEMA, conform


class PartitionedTable:
    """A directory of immutable Parquet part files sharing one schema."""

    def __init__(self, directory: Path, schema: dict[str, pl.DataType]) -> None:
        self.directory = directory
        self.schema = schema

    def append(self, df: pl.DataFrame, ingested_at: datetime) -> Path | None:
        if df.is_empty():
            return None
        df = conform(df, self.schema)
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = ingested_at.strftime("%Y%m%dT%H%M%S%fZ")
        path = self.directory / f"part-{stamp}-{uuid.uuid4().hex[:8]}.parquet"
        tmp = path.with_suffix(".tmp")
        df.write_parquet(tmp)
        tmp.rename(path)
        return path

    def read_all_versions(self) -> pl.DataFrame:
        parts = sorted(self.directory.glob("part-*.parquet"))
        if not parts:
            return pl.DataFrame(schema=self.schema)
        return conform(pl.concat([pl.read_parquet(p) for p in parts]), self.schema)

    def read_latest(self, key: list[str], where: pl.Expr | None = None) -> pl.DataFrame:
        """Latest version per ``key``, considering only versions matching ``where``."""
        versions = self.read_all_versions()
        if where is not None:
            versions = versions.filter(where)
        return (
            versions.sort("ingested_at")
            .unique(subset=key, keep="last", maintain_order=True)
            .sort(key)
        )


class DataStore:
    """Root of the local market data lake."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.bars = PartitionedTable(root / "bars", BAR_SCHEMA)
        self.instruments = PartitionedTable(root / "instruments", INSTRUMENT_SCHEMA)

    def latest_bars(self) -> pl.DataFrame:
        """Latest final version of every bar (see ``FINAL_BAR``)."""
        return self.bars.read_latest(BAR_KEY, where=FINAL_BAR)
