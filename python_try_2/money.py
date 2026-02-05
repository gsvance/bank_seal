"""Exact dollar amounts implemented as a wrapper around an int value.

Last modified 26 Jun 2023 by Greg Vance.
"""


import re
from typing import Any, Dict, Union

from comma_int import parse_comma_int, render_comma_int


DOLLAR_CENTS = 100  # Number of cents that make up one dollar

MONEY_FORMAT_REGEX = re.compile(r"""
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


class Money:
    """Nicely represents an amount of money in dollars and cents exactly. The
    internally stored value is an exact integer number of cents. Other features
    include nice parsing and printing of monetary strings.
    """

    __slots__ = ("_cents",)

    # Constructors

    def __init__(self, cents: int) -> None:
        self._cents = cents

    @classmethod
    def parse(cls, s: str) -> 'Money':

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

        return Money(sign * (dollars * DOLLAR_CENTS + cents))

    @classmethod
    def from_numeric(cls, n: float, picky: bool = True) -> 'Money':
        """Interpret a numeric type as Money by rounding to the nearest cent.

        Construct a new Money object whose value in dollars and cents is given
        by n, which can be a float or an int. If picky is True (default
        behavior), then the input *must* be as near as possible to an exact
        multiple of 1 cent, such that float(Money.from_numeric(n)) == n. If
        picky is False, then the input is simply rounded to the nearest cent
        without regard for whether the conversion is reversible.
        """
        # The round() function returns an int when ndigits is omitted
        money = Money(round(n * DOLLAR_CENTS))

        if not picky or float(money) == n:
            return money
        else:
            raise ValueError(f"cannot convert {n!r} to Money with picky=True")

    @classmethod
    def deserialize(cls, obj: Dict[str, Any]) -> 'Money':
        """Reconstruct Money which was serialized to a JSON object (dict)."""
        assert set(obj.keys()) == {"class", "cents"}
        assert obj["class"] == "Money"
        assert isinstance(obj["cents"], int)
        return Money(obj["cents"])

    # Output methods

    def __str__(self) -> str:
        sign_string = "-" if self.sign == -1 else ""
        dollars_string = render_comma_int(self.unsigned_dollars)
        cents_string = str(self.unsigned_cents).zfill(2)
        return f"{sign_string}${dollars_string}.{cents_string}"

    def __repr__(self) -> str:
        return f"Money({self._cents})"

    def serialize(self) -> Dict[str, Any]:
        """Convert Money to a dict (object) that JSON can comprehend."""
        return {"class": "Money", "cents": self._cents}

    # Properties for controlled access to internals

    @property
    def sign(self) -> int:
        if self._cents > 0:
            return +1
        elif self._cents < 0:
            return -1
        else:
            return 0

    @property
    def unsigned_dollars(self) -> int:
        return abs(self._cents) // DOLLAR_CENTS

    @property
    def unsigned_cents(self) -> int:
        return abs(self._cents) % DOLLAR_CENTS

    @property
    def in_pennies(self) -> int:
        return self._cents

    # Conversions to Python numeric types

    def __float__(self) -> float:
        return self._cents / float(DOLLAR_CENTS)

    def __int__(self) -> int:
        if self._cents >= 0:
            # Floor positive numbers towards zero
            return self._cents // DOLLAR_CENTS
        else:
            # Ceil negative numbers towards zero
            return -(-self._cents // DOLLAR_CENTS)

    def __bool__(self) -> bool:
        return self._cents != 0

    # Comparisons

    def _compare(self, other: Union['Money', float]) -> int:
        # Basically an old C-style cmp() function for doing comparisons
        # Also handles any conversions to Money from other numeric types
        if isinstance(other, Money):
            return self._cents - other._cents
        else:
            # Note: the setting picky=True right here is essential for making
            # the Money class hashable according to Python's hashing rules.
            other_as_money = Money.from_numeric(other, picky=True)
            return self._cents - other_as_money._cents

    def __lt__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) < 0

    def __le__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) <= 0

    def __eq__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) == 0

    def __ne__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) != 0

    def __gt__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: Union['Money', float]) -> bool:
        return self._compare(other) >= 0

    # Unary math operations

    def __pos__(self) -> 'Money':
        return Money(+self._cents)

    def __neg__(self) -> 'Money':
        return Money(-self._cents)

    def __abs__(self) -> 'Money':
        return Money(abs(self._cents))

    # Binary arithmetic operations

    def __add__(self, other: Union['Money', float]) -> 'Money':
        if isinstance(other, Money):
            return Money(self._cents + other._cents)
        else:
            other_as_money = Money.from_numeric(other, picky=False)
            return Money(self._cents + other_as_money._cents)

    def __sub__(self, other: Union['Money', float]) -> 'Money':
        return self + -other

    def __mul__(self, other: int) -> 'Money':
        return Money(self._cents * other)

    # Reflected binary arithmetic operations

    def __radd__(self, other: float) -> 'Money':
        return self + other

    def __rsub__(self, other: float) -> 'Money':
        return -self + other

    def __rmul__(self, other: int) -> 'Money':
        return self * other

    # Augmented assignment

    def __iadd__(self, other: Union['Money', float]) -> 'Money':
        return self + other

    def __isub__(self, other: Union['Money', float]) -> 'Money':
        return self - other

    def __imul__(self, other: int) -> 'Money':
        return self * other

    # Other methods

    def __hash__(self) -> int:
        # Objects that compare equal in Python must have the same hash value.
        # Since Money objects can be compared with floats and ints, we want to
        # hash float(self) in this method to ensure that holds. This has the
        # potential for all sorts of contradictions, which are prevented by the
        # use of Money.from_numeric() with the picky=True setting inside the
        # _compare() method.
        return hash(float(self))
