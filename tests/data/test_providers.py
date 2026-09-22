from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from swing.data.providers import CsvProvider, ProviderError
from swing.data.providers.yahoo import normalize_yahoo

NY = ZoneInfo("America/New_York")


def test_normalize_yahoo_uses_exchange_date_and_drops_nan_rows() -> None:
    index = [datetime(2024, 1, 2, 0, 0, tzinfo=NY), datetime(2024, 1, 3, 0, 0, tzinfo=NY)]
    nan = float("nan")
    df = normalize_yahoo(
        index,
        {
            "Open": [1.0, nan],
            "High": [2.0, nan],
            "Low": [0.5, nan],
            "Close": [1.5, nan],
            "Volume": [100.0, nan],
        },
    )
    assert df.get_column("date").to_list() == [date(2024, 1, 2)]
    assert df.get_column("close").to_list() == [1.5]


def test_normalize_yahoo_does_not_shift_date_via_utc() -> None:
    # Midnight New York is 05:00 UTC the same day; the date must stay the exchange date.
    ts = datetime(2024, 1, 2, 0, 0, tzinfo=NY)
    assert ts.astimezone(UTC).date() == date(2024, 1, 2)
    df = normalize_yahoo([ts], {k: [1.0] for k in ("Open", "High", "Low", "Close", "Volume")})
    assert df.get_column("date").to_list() == [date(2024, 1, 2)]


def test_csv_provider_reads_and_filters_range(tmp_path: Path) -> None:
    (tmp_path / "AAA.csv").write_text(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,1,2,0.5,1.5,100\n"
        "2024-01-03,1.5,2.5,1,2,200\n"
        "2024-01-04,2,3,1.5,2.5,300\n"
    )
    df = CsvProvider(tmp_path).fetch_daily_bars("aaa", date(2024, 1, 3), date(2024, 1, 4))
    assert df.get_column("date").to_list() == [date(2024, 1, 3), date(2024, 1, 4)]
    assert df.get_column("volume").to_list() == [200.0, 300.0]


def test_csv_provider_missing_column_raises_provider_error(tmp_path: Path) -> None:
    (tmp_path / "AAA.csv").write_text("date,close\n2024-01-02,1.5\n")
    with pytest.raises(ProviderError):
        CsvProvider(tmp_path).fetch_daily_bars("AAA", date(2024, 1, 1), date(2024, 1, 31))


def test_csv_provider_missing_file_raises_provider_error(tmp_path: Path) -> None:
    with pytest.raises(ProviderError):
        CsvProvider(tmp_path).fetch_daily_bars("NOPE", date(2024, 1, 1), date(2024, 1, 31))
