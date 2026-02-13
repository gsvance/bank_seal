"""Exact dollar amounts as a dataclass wrapper around an int value."""

import dataclasses
import re
from typing import Any, Final, Self

from comma_int import parse_comma_int, render_comma_int


# The number of cents that make up one dollar
DOLLAR_CENTS: Final[int] = 100


# Regex to match the format of money strings
MONEY_FORMAT_REGEX: Final[re.Pattern[str]] = re.compile(r"""
    \A\s*               # Optional whitespace at start
    (?P<sign>[-+]?)     # then an optional +/- sign
    \$?                 # and an optional $ before any digits
    (?=\d|\.\d)         # Numerical part begins with digit or .digit
    (?P<dollars>        # The integer dollars part consists of
        [\d,]*          # a (possibly empty) string of digits and commas
                        # which greedy-matches as much as possible
    ) \.?               # and is followed by an optional decimal point
                        # If digits remain after the integer part matches
    (?P<cents>          # then the optional fractional cents part
        \d{0,2}         # can match up to two additional digits
    )
    \s*\Z               # More optional whitespace at end
""", re.VERBOSE)


@dataclasses.dataclass(
    repr=False,
    order=True,
    frozen=True,
    match_args=False,
    slots=True,
)
class Money:
    """Nicely represents an amount of money in dollars and cents exactly.

    The internally stored value is an exact integer number of cents. Other
    features include nice parsing and printing of monetary strings.
    """
    cents: int

    # Constructors

    @classmethod
    def parse(cls, s: str) -> Self:
        """Parse a Money object from a string representation."""

        regex_match = MONEY_FORMAT_REGEX.fullmatch(s)
        if not regex_match:
            raise ValueError(f"failed to parse amount of money: {s!r}")

        # Map sign characters '+' and '-' to the ints +/- 1
        # The empty string is equivalent to '+'
        sign_character = regex_match.group("sign")
        sign = int(f"{sign_character}1")

        # Pad dollars_string with leading zeros up to a length of 1
        # This just makes it so that "" becomes "0" which parses as 0
        dollars_string = regex_match.group("dollars").rjust(1, '0')
        dollars = parse_comma_int(dollars_string)

        # Pad cents_string with zeros on the right out to a length of 2
        # That way "$1." becomes "$1.00" and "$1.2" becomes "$1.20"
        # Otherwise, "$1.2" would be parsed as one dollar and TWO cents
        cents_string = regex_match.group("cents").ljust(2, '0')
        cents = int(cents_string)

        return cls(sign * (dollars * DOLLAR_CENTS + cents))

    @classmethod
    def deserialize(cls, obj: dict[str, Any]) -> Self:
        """Reconstruct Money which was serialized to a JSON object (dict)."""
        assert set(obj.keys()) == {"class", "cents"}
        assert obj["class"] == "Money"
        assert isinstance(obj["cents"], int)
        return cls(obj["cents"])

    # Output methods

    def __str__(self) -> str:
        sign_string = "-" if self.sign == -1 else ""
        dollars_string = render_comma_int(self.unsigned_dollars)
        cents_string = str(self.unsigned_cents).zfill(2)
        return f"{sign_string}${dollars_string}.{cents_string}"

    def __repr__(self) -> str:
        return f"Money({self.cents})"

    def serialize(self) -> dict[str, Any]:
        """Convert Money to a dict (object) that JSON can comprehend."""
        return {"class": "Money", "cents": self.cents}

    # Properties for controlled access to internals

    @property
    def sign(self) -> int:
        if self.cents > 0:
            return +1
        if self.cents < 0:
            return -1
        return 0

    @property
    def unsigned_dollars(self) -> int:
        return abs(self.cents) // DOLLAR_CENTS

    @property
    def unsigned_cents(self) -> int:
        return abs(self.cents) % DOLLAR_CENTS

    @property
    def in_pennies(self) -> int:
        return self.cents

    # Unary math operations

    def __neg__(self) -> Self:
        return self.__class__(-self.cents)

    def __abs__(self) -> Self:
        return self.__class__(abs(self.cents))

    # Binary arithmetic operations

    def __add__(self, other: Self) -> Self:
        return self.__class__(self.cents + other.cents)

    def __sub__(self, other: Self) -> Self:
        return self + -other

    def __mul__(self, other: int) -> Self:
        return self.__class__(self.cents * other)

    # Reflected binary arithmetic operations

    def __rmul__(self, other: int) -> Self:
        return self * other

    # Augmented assignment

    def __iadd__(self, other: Self) -> Self:
        return self + other

    def __isub__(self, other: Self) -> Self:
        return self - other

    def __imul__(self, other: int) -> Self:
        return self * other
