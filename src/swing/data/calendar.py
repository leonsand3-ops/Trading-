"""US equity session timing."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
REGULAR_CLOSE = time(16, 0)


def session_close_utc(day: date) -> datetime:
    """Regular session close for ``day`` in UTC.

    Early-close days (13:00) are treated as 16:00, which only makes data appear later
    than it really was, never earlier.
    """
    return datetime.combine(day, REGULAR_CLOSE, tzinfo=NEW_YORK).astimezone(UTC)


def new_york_date(ts: datetime) -> date:
    """Calendar date in New York at ``ts``."""
    return ts.astimezone(NEW_YORK).date()


def latest_final_session(now: datetime) -> date:
    """Most recent weekday whose bar can be final at ``now`` (see ``FINAL_BAR``).

    US market holidays are not known here, so after a holiday this names the holiday.
    """
    day = new_york_date(now) - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day
