"""Look-ahead protection. These tests guard the core promise of the data layer."""

from datetime import UTC, date, datetime

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from swing.data.asof import BarHistory
from swing.data.ingest import ingest_bars
from swing.data.store import DataStore
from tests.conftest import FakeProvider, make_raw_bars, weekdays

START = date(2024, 1, 1)
N = 60
DAYS = weekdays(START, N)
NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _history(store: DataStore) -> BarHistory:
    provider = FakeProvider(
        {"AAA": make_raw_bars(START, N), "BBB": make_raw_bars(START, N, first_close=20.0)}
    )
    ingest_bars(provider, ["AAA", "BBB"], START, DAYS[-1], store, NOW)
    return BarHistory.load(store)


def test_view_at_close_contains_that_day_but_nothing_later(store: DataStore) -> None:
    view = _history(store).at_close(DAYS[10])
    assert view.all_bars().get_column("date").max() == DAYS[10]


def test_bar_is_invisible_one_minute_before_close(store: DataStore) -> None:
    history = _history(store)
    before_close = datetime(2024, 1, 15, 20, 59, tzinfo=UTC)  # 15:59 New York
    assert history.as_of(before_close).all_bars().get_column("date").max() == date(2024, 1, 12)


def test_naive_timestamp_is_rejected(store: DataStore) -> None:
    with pytest.raises(ValueError):
        _history(store).as_of(datetime(2024, 1, 15))


def test_lookback_returns_most_recent_bars(store: DataStore) -> None:
    history = _history(store)
    view = history.at_close(DAYS[20])
    instrument_id = view.instrument_ids()[0]
    assert view.bars(instrument_id, lookback=5).get_column("date").to_list() == DAYS[16:21]


@settings(max_examples=30, deadline=None)
@given(t=st.sampled_from(DAYS))
def test_truncation_view_does_not_depend_on_later_history(t: date) -> None:
    """A view at t is identical whether or not data after t exists."""
    full = make_raw_bars(START, N)
    truncated = full.filter(pl.col("date") <= t)
    views = []
    for data in (full, truncated):
        bars = _as_stored(data)
        views.append(BarHistory(bars).at_close(t).all_bars())
    assert views[0].equals(views[1])


@settings(max_examples=30, deadline=None)
@given(t=st.sampled_from(DAYS))
def test_future_poisoning_does_not_change_view(t: date) -> None:
    """Replacing everything after t with nonsense leaves the view at t untouched."""
    clean = make_raw_bars(START, N)
    poisoned = clean.with_columns(
        [
            pl.when(pl.col("date") > t).then(pl.lit(-999.0)).otherwise(pl.col(c)).alias(c)
            for c in ("open", "high", "low", "close", "volume")
        ]
    )
    a = BarHistory(_as_stored(clean)).at_close(t).all_bars()
    b = BarHistory(_as_stored(poisoned)).at_close(t).all_bars()
    assert a.equals(b)


def _as_stored(raw: pl.DataFrame) -> pl.DataFrame:
    """Run raw bars through the real ingest path into a throwaway store."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = DataStore(Path(tmp))
        ingest_bars(FakeProvider({"AAA": raw}), ["AAA"], START, DAYS[-1], store, NOW)
        # Instrument ids are random per store, so leave them out of comparisons.
        return (
            store.latest_bars()
            .drop("instrument_id")
            .with_columns(pl.lit("ins_test").alias("instrument_id"))
        )
