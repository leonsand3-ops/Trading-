"""Data quality checks on resolved daily bars.

Errors mean the data must not be used for research until fixed. Warnings need a look
but are often real market behaviour (halts, genuine large moves).
"""

import datetime as dt
from enum import StrEnum

import polars as pl
from pydantic import BaseModel

SPLIT_RATIOS = (2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 20.0)
SPLIT_TOLERANCE = 0.03
LARGE_MOVE = 0.40
STALE_RUN = 5
# A date counts as a trading session if at least this share of instruments have a bar.
SESSION_COVERAGE = 0.5


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class QualityIssue(BaseModel):
    instrument_id: str
    check: str
    severity: Severity
    date: dt.date | None = None
    detail: str = ""


def _issues(df: pl.DataFrame, check: str, severity: Severity, detail: str) -> list[QualityIssue]:
    return [
        QualityIssue(
            instrument_id=row["instrument_id"],
            check=check,
            severity=severity,
            date=row["date"],
            detail=detail.format(**row),
        )
        for row in df.iter_rows(named=True)
    ]


def check_bars(bars: pl.DataFrame) -> list[QualityIssue]:
    """Run all checks on bars with at least instrument_id, date and OHLCV columns."""
    if bars.is_empty():
        return []
    bars = bars.sort(["instrument_id", "date"])
    issues: list[QualityIssue] = []

    issues += _issues(
        bars.filter(pl.min_horizontal("open", "high", "low", "close") <= 0),
        "nonpositive_price",
        Severity.ERROR,
        "close={close}",
    )
    issues += _issues(
        bars.filter(
            (pl.col("high") < pl.max_horizontal("open", "close", "low"))
            | (pl.col("low") > pl.min_horizontal("open", "close", "high"))
        ),
        "ohlc_inconsistent",
        Severity.ERROR,
        "o={open} h={high} l={low} c={close}",
    )
    issues += _issues(
        bars.filter(pl.col("volume") < 0), "negative_volume", Severity.ERROR, "volume={volume}"
    )
    issues += _issues(
        bars.filter(pl.col("volume") == 0), "zero_volume", Severity.WARNING, "close={close}"
    )

    moves = bars.with_columns(
        (pl.col("close") / pl.col("close").shift(1).over("instrument_id")).alias("ratio")
    ).filter(pl.col("ratio").is_not_null())
    ratio_expr = pl.max_horizontal(pl.col("ratio"), 1 / pl.col("ratio"))
    near_split = pl.any_horizontal(
        [(ratio_expr / r - 1).abs() < SPLIT_TOLERANCE for r in SPLIT_RATIOS]
    )
    issues += _issues(
        moves.filter(near_split),
        "possible_unadjusted_split",
        Severity.ERROR,
        "close ratio {ratio:.3f} vs previous day",
    )
    issues += _issues(
        moves.filter(~near_split & ((pl.col("ratio") - 1).abs() > LARGE_MOVE)),
        "large_move",
        Severity.WARNING,
        "close ratio {ratio:.3f} vs previous day",
    )

    runs = (
        bars.with_columns(
            (pl.col("close") != pl.col("close").shift(1).over("instrument_id"))
            .fill_null(True)
            .cum_sum()
            .over("instrument_id")
            .alias("run_id")
        )
        .group_by("instrument_id", "run_id")
        .agg(pl.len().alias("length"), pl.col("date").first())
        .filter(pl.col("length") >= STALE_RUN)
        .sort("instrument_id", "date")
    )
    issues += _issues(runs, "stale_close", Severity.WARNING, "close unchanged for {length} days")

    issues += _missing_sessions(bars)
    return issues


def _missing_sessions(bars: pl.DataFrame) -> list[QualityIssue]:
    """Sessions inside an instrument's date range where it has no bar."""
    n_instruments = bars.get_column("instrument_id").n_unique()
    sessions = (
        bars.group_by("date")
        .agg(pl.col("instrument_id").n_unique().alias("n"))
        .filter(pl.col("n") >= SESSION_COVERAGE * n_instruments)
        .select("date")
    )
    spans = bars.group_by("instrument_id").agg(
        pl.col("date").min().alias("first"), pl.col("date").max().alias("last")
    )
    expected = spans.join(sessions, how="cross").filter(
        pl.col("date").is_between(pl.col("first"), pl.col("last"))
    )
    missing = expected.join(
        bars.select("instrument_id", "date"), on=["instrument_id", "date"], how="anti"
    )
    return _issues(
        missing.sort("instrument_id", "date"),
        "missing_session",
        Severity.WARNING,
        "no bar on a session most instruments traded",
    )
