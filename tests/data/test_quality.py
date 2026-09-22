from datetime import date

import polars as pl

from swing.data.quality import Severity, check_bars
from tests.conftest import make_raw_bars

START = date(2024, 1, 1)


def _bars(raw: pl.DataFrame, instrument_id: str = "ins_a") -> pl.DataFrame:
    return raw.with_columns(pl.lit(instrument_id).alias("instrument_id"))


def _set(raw: pl.DataFrame, row: int, **values: float) -> pl.DataFrame:
    idx = pl.int_range(pl.len())
    return raw.with_columns(
        [
            pl.when(idx == row).then(pl.lit(v)).otherwise(pl.col(c)).alias(c)
            for c, v in values.items()
        ]
    )


def _checks(bars: pl.DataFrame) -> set[str]:
    return {i.check for i in check_bars(bars)}


def test_clean_data_has_no_issues() -> None:
    assert check_bars(_bars(make_raw_bars(START, 30))) == []


def test_nonpositive_price_is_error() -> None:
    issues = check_bars(_bars(_set(make_raw_bars(START, 10), 3, low=0.0)))
    assert any(i.check == "nonpositive_price" and i.severity == Severity.ERROR for i in issues)


def test_high_below_close_is_inconsistent() -> None:
    assert "ohlc_inconsistent" in _checks(_bars(_set(make_raw_bars(START, 10), 3, high=90.0)))


def test_zero_volume_is_warning() -> None:
    issues = check_bars(_bars(_set(make_raw_bars(START, 10), 3, volume=0.0)))
    assert [(i.check, i.severity) for i in issues] == [("zero_volume", Severity.WARNING)]


def test_halving_close_flags_possible_unadjusted_split() -> None:
    raw = make_raw_bars(START, 10, step=0.0)
    raw = raw.with_columns(
        [
            pl.when(pl.int_range(pl.len()) >= 5).then(pl.col(c) / 2).otherwise(pl.col(c)).alias(c)
            for c in ("open", "high", "low", "close")
        ]
    )
    issues = [i for i in check_bars(_bars(raw)) if i.check == "possible_unadjusted_split"]
    assert len(issues) == 1
    assert issues[0].date == date(2024, 1, 8)


def test_large_non_split_move_is_warning() -> None:
    raw = _set(
        make_raw_bars(START, 10, step=0.0), 5, open=150.0, high=156.0, low=149.0, close=155.0
    )
    assert "large_move" in _checks(_bars(raw))


def test_unchanged_close_for_five_days_is_stale() -> None:
    assert "stale_close" in _checks(_bars(make_raw_bars(START, 10, step=0.0)))


def test_missing_session_detected_against_other_instruments() -> None:
    full = make_raw_bars(START, 20)
    gappy = full.filter(pl.col("date") != date(2024, 1, 10))
    bars = pl.concat([_bars(full, "ins_a"), _bars(full, "ins_b"), _bars(gappy, "ins_c")])
    issues = [i for i in check_bars(bars) if i.check == "missing_session"]
    assert [(i.instrument_id, i.date) for i in issues] == [("ins_c", date(2024, 1, 10))]
