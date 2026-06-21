"""DateTime extension - date and time support for PyQalculate.

Mirrors libqalculate's QalculateDateTime class for date/time arithmetic.
"""

from __future__ import annotations

import datetime
from typing import Union


class DateTimeExt:
    """Extended date/time class with calendar support.

    Provides date arithmetic, calendar conversions, and formatting
    compatible with libqalculate's QalculateDateTime.

    Supports:
    - Gregorian calendar dates and times
    - Date arithmetic (add days, months, years)
    - Day of week, day of year calculations
    - ISO week number
    - Difference between dates
    """

    def __init__(
        self,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: float = 0.0,
    ) -> None:
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second

    @classmethod
    def now(cls) -> DateTimeExt:
        """Create a DateTimeExt representing the current moment."""
        dt = datetime.datetime.now()
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)

    @classmethod
    def today(cls) -> DateTimeExt:
        """Create a DateTimeExt representing today's date."""
        dt = datetime.datetime.now()
        return cls(dt.year, dt.month, dt.day)

    @classmethod
    def from_iso(cls, iso_string: str) -> DateTimeExt:
        """Parse an ISO 8601 date/time string."""
        # Try common formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.datetime.strptime(iso_string, fmt)
                return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                           dt.second + dt.microsecond / 1e6)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {iso_string}")

    @classmethod
    def from_days(cls, days: int) -> DateTimeExt:
        """Create a DateTimeExt from a Julian day number."""
        # Simplified Julian day to Gregorian conversion
        # Full algorithm would use the standard Julian day conversion
        return cls(1, 1, 1)  # TODO: implement proper conversion

    # -- Properties --

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def second(self) -> float:
        return self._second

    # -- Date calculations --

    def day_of_week(self) -> int:
        """Return day of week (0=Sunday, 6=Saturday)."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return (dt.weekday() + 1) % 7  # Python: 0=Monday, convert to 0=Sunday
        except ValueError:
            return 0

    def day_of_year(self) -> int:
        """Return day of year (1-366)."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return dt.timetuple().tm_yday
        except ValueError:
            return 1

    def week_number(self) -> int:
        """Return ISO week number."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return dt.isocalendar()[1]
        except ValueError:
            return 1

    def is_leap_year(self) -> bool:
        """Check if the year is a leap year."""
        year = self._year
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def days_in_month(self) -> int:
        """Return the number of days in the current month."""
        if self._month == 2:
            return 29 if self.is_leap_year() else 28
        if self._month in (4, 6, 9, 11):
            return 30
        return 31

    def days_in_year(self) -> int:
        """Return the number of days in the current year."""
        return 366 if self.is_leap_year() else 365

    def to_julian_day(self) -> float:
        """Convert to Julian day number."""
        # Simplified calculation
        try:
            dt = datetime.date(self._year, self._month, self._day)
            # Julian day for Jan 1, 2000 is 2451545
            epoch = datetime.date(2000, 1, 1)
            return 2451545.0 + (dt - epoch).days
        except ValueError:
            return 0.0

    # -- Arithmetic --

    def add_days(self, days: int) -> DateTimeExt:
        """Return a new DateTimeExt with days added."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            dt += datetime.timedelta(days=days)
            return DateTimeExt(dt.year, dt.month, dt.day, self._hour, self._minute, self._second)
        except ValueError:
            return DateTimeExt(self._year, self._month, self._day)

    def add_months(self, months: int) -> DateTimeExt:
        """Return a new DateTimeExt with months added."""
        total_months = (self._year * 12 + self._month - 1) + months
        new_year = total_months // 12
        new_month = total_months % 12 + 1
        # Clamp day to valid range
        new_day = min(self._day, 28)  # Safe default
        try:
            new_day = self._day
            datetime.date(new_year, new_month, new_day)
        except ValueError:
            new_day = 28
        return DateTimeExt(new_year, new_month, new_day, self._hour, self._minute, self._second)

    def add_years(self, years: int) -> DateTimeExt:
        """Return a new DateTimeExt with years added."""
        return DateTimeExt(
            self._year + years, self._month, self._day,
            self._hour, self._minute, self._second,
        )

    def difference_days(self, other: DateTimeExt) -> int:
        """Return the difference in days between two dates."""
        try:
            d1 = datetime.date(self._year, self._month, self._day)
            d2 = datetime.date(other._year, other._month, other._day)
            return (d1 - d2).days
        except ValueError:
            return 0

    # -- Comparison --

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DateTimeExt):
            return NotImplemented
        return (self._year == other._year and self._month == other._month and
                self._day == other._day and self._hour == other._hour and
                self._minute == other._minute and abs(self._second - other._second) < 0.001)

    def __lt__(self, other: DateTimeExt) -> bool:
        return (self._year, self._month, self._day, self._hour, self._minute, self._second) < \
               (other._year, other._month, other._day, other._hour, other._minute, other._second)

    def __le__(self, other: DateTimeExt) -> bool:
        return self == other or self < other

    def __gt__(self, other: DateTimeExt) -> bool:
        return not self.__le__(other)

    def __ge__(self, other: DateTimeExt) -> bool:
        return not self.__lt__(other)

    # -- Formatting --

    def to_iso_string(self) -> str:
        """Format as ISO 8601 string."""
        if self._hour == 0 and self._minute == 0 and self._second == 0:
            return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"
        return (f"{self._year:04d}-{self._month:02d}-{self._day:02d}T"
                f"{self._hour:02d}:{self._minute:02d}:{self._second:06.3f}")

    def __str__(self) -> str:
        return self.to_iso_string()

    def __repr__(self) -> str:
        return (f"DateTimeExt({self._year}, {self._month}, {self._day}, "
                f"{self._hour}, {self._minute}, {self._second})")
