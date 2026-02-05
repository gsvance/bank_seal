"""Implements the class used for representing calendar dates.

Last modified 26 Jun 2023 by Greg Vance.
"""


import datetime
import re
from typing import Any, Dict, Tuple


YEAR_MIN = 1980  # Earliest acceptable year (used for sanity checking)
YEAR_MAX = 2100  # Latest acceptable year (also used for sanity checking)

MONTH_MIN = 1
MONTH_MAX = 12
MONTH_COUNT = MONTH_MAX - MONTH_MIN + 1
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
MONTH_NUMBERS = {name: number for (number, name) in MONTH_NAMES.items()}

DAY_MIN = 1
DAYS_IN_MONTH = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}
LEAP_DAY_MONTH = 2  # February is the month that gets a leap day

# Match dates using the tradional American format "m/d/y"
DATE_FORMAT_REGEX_USA = re.compile(r"""
    \A\s*           # Optional leading whitespace
    (?P<month>      # The month comes first and consists of
        \d{1,2}     # either one or two digits
    )
    /               # Month and day are separated by '/'
    (?P<day>        # The day comes second and also consists of
        \d{1,2}     # either one or two digits
    )
    (?: /           # Day and year are separated by '/'
    (?P<year>       # The year comes last and consists of
        \d{2}|\d{4} # either two or four digits
    ) )?            # The whole /year bit is actually optional
    \s*\Z           # Optional trailing whitespace
""", re.VERBOSE)

# Match dates using the more international format "d mmm y"
DATE_FORMAT_REGEX_INTL = re.compile(r"""
    \A\s*               # Optional leading whitespace
    (?P<day>            # First comes the day, which consists of
        \d{1,2}         # either one or two digits
    )
    [ ]+                # One or more space characters between day and month
    (?P<month>          # Second is the month, which is written as
        [A-Z][a-z]{2}   # a title-case sequence of three letters
    )
    (?: [ ]+            # One or more space characters between month and year
    (?P<year>           # Last is the year, which can be
        \d{2}|\d{4}     # either two or four digits
    ) )?                # The whole spaces + year bit is actually optional
    \s*\Z               # Optional trailing whitespace
""", re.VERBOSE)


class Date:
    """Relatively simple custom class representing a calendar date.

    It has a bunch of sanity checks, a nice string representation, and the
    ability to chronologically order itself relative to other instances.
    Objects of this class are hashable and should be treated as immutable.
    """

    __slots__ = ("_year", "_month", "_day")

    # Constructors

    def __init__(self, year: int, month: int, day: int) -> None:
        self._year = year  # Full four-digit year
        self._month = month
        self._day = day
        self._validate()

    @classmethod
    def today(cls) -> 'Date':
        """Construct a new Date object using today's date.

        The current date is obtained using the built-in datetime module.
        """
        dt_date = datetime.date.today()
        return Date(dt_date.year, dt_date.month, dt_date.day)

    @classmethod
    def infer_year(cls, year_hint: None | int, month: int, day: int) -> 'Date':
        """Create a new Date object with incomplete year information.

        Return a Date having the given month and day, but whose year is
        inferred from the provided year hint. If the hint is a four-digit int,
        then it becomes the year. If the hint is an int in the closed interval
        [0, 99], then it is interpreted as a two-digit year, and the returned
        year is chosen to be as close as possible to the current year. If the
        year hint is None, then the year is chosen such that the returned
        month and year is as close as possible to the current month and year.
        """
        if isinstance(year_hint, int) and 1000 <= year_hint <= 9999:
            four_digit_year = year_hint
            return Date(four_digit_year, month, day)

        elif isinstance(year_hint, int) and 0 <= year_hint <= 99:
            two_digit_year = year_hint

            # Figure out the current year and the century part of that year
            current_year = Date.today().year
            current_century = (current_year // 100) * 100

            # Given a two-digit year hint, we will infer a four-digit year by
            # picking a year that
            #   1) ends with the two-digit hint and
            #   2) is as close as possible to the current year.
            # The inferred century must then be either the current century or
            # an adjacent century. Pick whichever option yields the smallest
            # difference between the inferred year and the current year,
            # giving very slight preference to the current century and then
            # the past century over the future century. This preference comes
            # from the ordering of the list below, since min() returns the
            # first minimal element encountered in the event that it finds
            # more than one such element.
            century_options = [
                current_century, current_century - 100, current_century + 100
            ]
            inferred_century = min(
                century_options,
                key=lambda century: abs(
                    (century + two_digit_year) - current_year
                )
            )
            return Date(inferred_century + two_digit_year, month, day)

        elif year_hint is None:
            today = Date.today()
            current_year, current_month = today.year, today.month

            # Without a year hint of any kind, we will infer the four-digit
            # year to be the curent year or an adjacent year. The inferred
            # year will be selected such that the returned month and year are
            # as close as possible to the current month and year where the
            # closeness is measured in whole months. As with the four-digit
            # year hint, give slight preference to the current and past before
            # the future via the list ordering and the min() function.
            year_options = [current_year, current_year - 1, current_year + 1]
            inferred_year = min(
                year_options,
                key=lambda year: abs(
                    (year * MONTH_COUNT + month - MONTH_MIN)
                    - (current_year * MONTH_COUNT + current_month - MONTH_MIN)
                )
            )
            return Date(inferred_year, month, day)

        else:
            raise ValueError(f"year hint {year_hint!r} is not usable")

    @classmethod
    def parse(cls, s: str) -> 'Date':
        """Parse a Date object from one of two string representations.

        Return a new Date derived from parsing a string of the form "m/d/y" or
        "d mmm y" with possibly incomplete year information. That is, y may be
        a four-digit year, a two-digit year, or entirely absent. If y is
        absent, then the input should match one of the simplified "m/d" or
        "d mmm" formats. Incomplete year information is used to infer a
        four-digit year using the Date.infer_year() constructor.
        """
        regex_match_USA = DATE_FORMAT_REGEX_USA.fullmatch(s)
        regex_match_intl = DATE_FORMAT_REGEX_INTL.fullmatch(s)

        if regex_match_USA:
            month = int(regex_match_USA.group("month"))
            day = int(regex_match_USA.group("day"))
            year_group = regex_match_USA.group("year")
            year_hint = int(year_group) if (year_group is not None) else None
            return Date.infer_year(year_hint, month, day)

        elif regex_match_intl:
            day = int(regex_match_intl.group("day"))
            month_group = regex_match_intl.group("month")
            if month_group in MONTH_NUMBERS:
                month = MONTH_NUMBERS[month_group]
            else:
                raise ValueError(f"unknown month name: {month_group!r}")
            year_group = regex_match_intl.group("year")
            year_hint = int(year_group) if (year_group is not None) else None
            return Date.infer_year(year_hint, month, day)

        else:
            raise ValueError(f"failed to parse date: {s!r}")

    @classmethod
    def deserialize(cls, obj: Dict[str, Any]) -> 'Date':
        """Reconstruct a date which was serialized to a JSON object (dict)."""
        assert set(obj.keys()) == {"class", "year", "month", "day"}
        assert obj["class"] == "Date"
        assert isinstance(obj["year"], int)
        assert isinstance(obj["month"], int)
        assert isinstance(obj["day"], int)
        return Date(obj["year"], obj["month"], obj["day"])

    # Output methods

    def __str__(self) -> str:
        return f"{self._day} {self.name_of_month()} {self._year}"

    def __repr__(self) -> str:
        return f"Date({self._year}, {self._month}, {self._day})"

    def serialize(self) -> Dict[str, Any]:
        """Convert this date to a dict (object) that JSON can comprehend."""
        return {
            "class": "Date",
            "year": self._year,
            "month": self._month,
            "day": self._day,
        }

    # Calendar functions

    def _validate(self) -> None:
        # Run some calendar sanity checks and raise an error if any fail

        if self._year < YEAR_MIN:
            raise ValueError(f"year {self._year} is before {YEAR_MIN}")
        if self._year > YEAR_MAX:
            raise ValueError(f"year {self._year} is after {YEAR_MAX}")

        if self._month < MONTH_MIN or self._month > MONTH_MAX:
            raise ValueError(f"illegal month of the year: {self._month}")

        if self._day < DAY_MIN:
            raise ValueError(f"illegal day of the month: {self._day}")
        if self._day > self.length_of_month():
            raise ValueError(f"{self!s} is after the end of the month")

    def name_of_month(self) -> str:
        return MONTH_NAMES[self._month]

    def length_of_month(self) -> int:
        """Return the total number of days in this date's month.

        When necessary, use the date's year to account for leap days.
        """
        if self._month == LEAP_DAY_MONTH and self.in_leap_year():
            leap_day = 1
        else:
            leap_day = 0
        return DAYS_IN_MONTH[self._month] + leap_day

    def in_leap_year(self) -> bool:
        """Return whether this date is in a year that is a leap year."""
        multiple_of_4 = self._year % 4 == 0
        not_a_century = self._year % 100 != 0
        multiple_of_400 = self._year % 400 == 0
        return multiple_of_4 and (not_a_century or multiple_of_400)

    # Properties for attribute access

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    # Chronological ordering

    def _order_key(self) -> Tuple[int, int, int]:
        # Assemble a standard tuple that can be used for ordering Dates
        return (self._year, self._month, self._day)

    def __lt__(self, other: 'Date') -> bool:
        return self._order_key() < other._order_key()

    def __le__(self, other: 'Date') -> bool:
        return self._order_key() <= other._order_key()

    def __eq__(self, other: 'Date') -> bool:
        return self._order_key() == other._order_key()

    def __ne__(self, other: 'Date') -> bool:
        return self._order_key() != other._order_key()

    def __gt__(self, other: 'Date') -> bool:
        return self._order_key() > other._order_key()

    def __ge__(self, other: 'Date') -> bool:
        return self._order_key() >= other._order_key()

    # Other methods

    def __hash__(self) -> int:
        # Meh, go ahead and make Date objects hashable
        # It leans into my intent to treat them as immutable
        # And being able to use dates as dict keys might be useful
        return hash((self._year, self._month, self._day))
