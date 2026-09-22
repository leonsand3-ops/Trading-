"""US equity session timing."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
REGULAR_CLOSE = time(16, 0)


def session_close_utc(day: date) -> datetime:
    """Regular session close for ``day`` in UTC.

    Early-close days (13:00) are treated as 16:00, which only makes data appear later
    than it really was, never earlier.
    """
    return datetime.combine(day, REGULAR_CLOSE, tzinfo=NEW_YORK).astimezone(UTC)
