from datetime import UTC, date, datetime

import polars as pl
import pytest

from swing.data.calendar import session_close_utc
from swing.data.schema import BAR_SCHEMA, INSTRUMENT_SCHEMA, SchemaError
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


def _bar(day: date, close: float, ingested_at: datetime) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "instrument_id": ["ins_a"],
            "date": [day],
            "open": [close],
            "high": [close + 1],
            "low": [close - 1],
            "close": [close],
            "volume": [1000.0],
            "adjustment": ["split"],
            "source": ["yahoo"],
            "known_at": [session_close_utc(day)],
            "ingested_at": [ingested_at],
        },
        schema=BAR_SCHEMA,
    )


def test_latest_bars_ignores_versions_ingested_on_the_bar_date(store: DataStore) -> None:
    # The real case: Yahoo's provisional 2026-09-22 bars fetched at 17:43 New York time.
    day = date(2026, 9, 22)
    same_evening = datetime(2026, 9, 22, 21, 43, tzinfo=UTC)
    store.bars.append(_bar(day, 518.0, same_evening), same_evening)
    assert store.latest_bars().is_empty()

    next_day = datetime(2026, 9, 23, 14, 0, tzinfo=UTC)
    store.bars.append(_bar(day, 519.0, next_day), next_day)
    assert store.latest_bars().get_column("close").to_list() == [519.0]
