from datetime import UTC, datetime

import polars as pl
import pytest

from swing.data.schema import INSTRUMENT_SCHEMA, SchemaError
from swing.data.store import DataStore

T1 = datetime(2024, 1, 1, tzinfo=UTC)
T2 = datetime(2024, 2, 1, tzinfo=UTC)


def _instrument(symbol: str, instrument_id: str, at: datetime) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "instrument_id": [instrument_id],
            "source": ["x"],
            "symbol": [symbol],
            "ingested_at": [at],
        },
        schema=INSTRUMENT_SCHEMA,
    )


def test_append_never_overwrites_and_latest_version_wins(store: DataStore) -> None:
    store.instruments.append(_instrument("AAA", "old", T1), T1)
    store.instruments.append(_instrument("AAA", "new", T2), T2)

    assert store.instruments.read_all_versions().height == 2
    latest = store.instruments.read_latest(["source", "symbol"])
    assert latest.get_column("instrument_id").to_list() == ["new"]


def test_empty_append_writes_nothing(store: DataStore) -> None:
    assert store.instruments.append(pl.DataFrame(schema=INSTRUMENT_SCHEMA), T1) is None
    assert store.instruments.read_all_versions().is_empty()


def test_append_rejects_missing_columns(store: DataStore) -> None:
    with pytest.raises(SchemaError):
        store.instruments.append(pl.DataFrame({"symbol": ["AAA"]}), T1)
