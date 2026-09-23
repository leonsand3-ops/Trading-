from datetime import UTC, date, datetime

from swing.data.calendar import latest_final_session, session_close_utc


def test_session_close_in_summer_is_20_utc() -> None:
    assert session_close_utc(date(2024, 7, 1)) == datetime(2024, 7, 1, 20, 0, tzinfo=UTC)


def test_session_close_in_winter_is_21_utc() -> None:
    assert session_close_utc(date(2024, 1, 2)) == datetime(2024, 1, 2, 21, 0, tzinfo=UTC)


def test_latest_final_session_next_morning_is_previous_day() -> None:
    # Wednesday 2026-09-23 04:57 New York (the user's diagnostic run).
    assert latest_final_session(datetime(2026, 9, 23, 8, 57, tzinfo=UTC)) == date(2026, 9, 22)


def test_latest_final_session_on_session_evening_is_day_before() -> None:
    # Tuesday 2026-09-22 17:43 New York: Tuesday's bar is not final yet.
    assert latest_final_session(datetime(2026, 9, 22, 21, 43, tzinfo=UTC)) == date(2026, 9, 21)


def test_latest_final_session_skips_weekend() -> None:
    # Monday 2026-09-21 01:00 New York: the latest final bar is Friday's.
    assert latest_final_session(datetime(2026, 9, 21, 5, 0, tzinfo=UTC)) == date(2026, 9, 18)
