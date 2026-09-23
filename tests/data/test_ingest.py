from datetime import UTC, date, datetime

import polars as pl

from swing.data.ingest import incremental_starts, ingest_bars
from swing.data.store import DataStore
from tests.conftest import FakeProvider, make_raw_bars

START = date(2024, 1, 1)  # Monday
END = date(2024, 1, 31)


def test_stores_bars_with_known_at_at_session_close(store: DataStore) -> None:
    provider = FakeProvider({"AAA": make_raw_bars(START, 5)})
    result = ingest_bars(provider, ["AAA"], START, END, store, datetime(2024, 2, 1, tzinfo=UTC))

    assert result.rows_written == {"AAA": 5}
    bars = store.latest_bars()
    first = bars.row(0, named=True)
    assert first["date"] == START
    assert first["known_at"] == datetime(2024, 1, 1, 21, 0, tzinfo=UTC)
    assert set(bars.get_column("source")) == {"fake"}


def test_drops_bar_whose_session_has_not_closed(store: DataStore) -> None:
    provider = FakeProvider({"AAA": make_raw_bars(START, 5)})  # Jan 1..5
    # 15:00 New York on Jan 5: the Jan 5 bar is still an intraday snapshot.
    now = datetime(2024, 1, 5, 20, 0, tzinfo=UTC)
    ingest_bars(provider, ["AAA"], START, END, store, now)

    assert store.latest_bars().get_column("date").max() == date(2024, 1, 4)


def test_unknown_symbol_is_reported_not_raised(store: DataStore) -> None:
    result = ingest_bars(
        FakeProvider({}), ["ZZZ"], START, END, store, datetime(2024, 2, 1, tzinfo=UTC)
    )
    assert "ZZZ" in result.failures
    assert store.latest_bars().is_empty()


def test_reingest_adds_version_and_latest_wins(store: DataStore) -> None:
    ingest_bars(
        FakeProvider({"AAA": make_raw_bars(START, 3)}),
        ["AAA"],
        START,
        END,
        store,
        datetime(2024, 2, 1, tzinfo=UTC),
    )
    revised = make_raw_bars(START, 3, first_close=50.0)
    ingest_bars(
        FakeProvider({"AAA": revised}), ["AAA"], START, END, store, datetime(2024, 3, 1, tzinfo=UTC)
    )

    assert store.bars.read_all_versions().height == 6
    latest = store.latest_bars()
    assert latest.height == 3
    assert latest.get_column("close").to_list() == [50.0, 51.0, 52.0]
    assert latest.get_column("instrument_id").n_unique() == 1


def test_duplicate_dates_from_provider_are_collapsed(store: DataStore) -> None:
    raw = make_raw_bars(START, 3)
    ingest_bars(
        FakeProvider({"AAA": pl.concat([raw, raw])}),
        ["AAA"],
        START,
        END,
        store,
        datetime(2024, 2, 1, tzinfo=UTC),
    )
    assert store.latest_bars().height == 3


def test_bar_is_stored_only_after_new_york_date_rolls_over(store: DataStore) -> None:
    provider = FakeProvider({"AAA": make_raw_bars(START, 5)})  # Mon Jan 1 .. Fri Jan 5
    evening_after_close = datetime(2024, 1, 5, 23, 0, tzinfo=UTC)  # 18:00 New York
    ingest_bars(provider, ["AAA"], START, END, store, evening_after_close)
    assert store.latest_bars().get_column("date").max() == date(2024, 1, 4)

    after_midnight_new_york = datetime(2024, 1, 6, 5, 30, tzinfo=UTC)  # 00:30 New York
    ingest_bars(provider, ["AAA"], START, END, store, after_midnight_new_york)
    assert store.latest_bars().get_column("date").max() == date(2024, 1, 5)


def test_incremental_starts_overlap_last_bar_and_default_for_new(store: DataStore) -> None:
    provider = FakeProvider({"AAA": make_raw_bars(START, 20)})  # last bar Jan 26
    ingest_bars(provider, ["AAA"], START, END, store, datetime(2024, 2, 1, tzinfo=UTC))

    starts = incremental_starts(store, "fake", ["AAA", "bbb"], date(2010, 1, 1))

    assert starts == {"AAA": date(2024, 1, 16), "BBB": date(2010, 1, 1)}


def test_per_symbol_start_limits_download(store: DataStore) -> None:
    provider = FakeProvider({"AAA": make_raw_bars(START, 20), "BBB": make_raw_bars(START, 20)})
    starts = {"AAA": date(2024, 1, 22), "BBB": START}
    result = ingest_bars(
        provider, ["AAA", "BBB"], starts, END, store, datetime(2024, 2, 1, tzinfo=UTC)
    )
    assert result.rows_written == {"AAA": 5, "BBB": 20}
