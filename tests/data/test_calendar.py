from datetime import UTC, date, datetime

from swing.data.calendar import session_close_utc


def test_session_close_in_summer_is_20_utc() -> None:
    assert session_close_utc(date(2024, 7, 1)) == datetime(2024, 7, 1, 20, 0, tzinfo=UTC)


def test_session_close_in_winter_is_21_utc() -> None:
    assert session_close_utc(date(2024, 1, 2)) == datetime(2024, 1, 2, 21, 0, tzinfo=UTC)
