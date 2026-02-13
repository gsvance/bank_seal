"""A collection of parser functions to be used with command signatures.

A parser (indicated by the generic Parser[R] type alias) is any callable that
takes a string and returns an instance of type R on success or None on failure.
"""

import typing

from date import Date
from money import Money
from name import Name


type Parser[R] = typing.Callable[[str], R | None]


def parse_str(s: str) -> str | None:
    return s


def parse_name(s: str) -> Name | None:
    try:
        return Name(s)
    except ValueError:
        return None


def parse_int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None


def parse_date(s: str) -> Date | None:
    try:
        return Date.parse(s)
    except ValueError:
        return None


def parse_money(s: str) -> Money | None:
    try:
        return Money.parse(s)
    except ValueError:
        return None


'''def parse_merchant(s: str) -> 'Merchant | None':
    pass'''


'''def parse_transaction(s: str) -> 'Transaction | None':
    pass'''


@typing.overload
def get_parser(parse_type: type[str]) -> Parser[str]: ...
@typing.overload
def get_parser(parse_type: type[Name]) -> Parser[Name]: ...
@typing.overload
def get_parser(parse_type: type[int]) -> Parser[int]: ...
@typing.overload
def get_parser(parse_type: type[Date]) -> Parser[Date]: ...
@typing.overload
def get_parser(parse_type: type[Money]) -> Parser[Money]: ...
@typing.overload
def get_parser[T](parse_type: type[T]) -> Parser[T]: ...


def get_parser(parse_type: type) -> Parser[object]:
    if parse_type is str:
        return parse_str
    if parse_type is Name:
        return parse_name
    if parse_type is int:
        return parse_int
    if parse_type is Date:
        return parse_date
    if parse_type is Money:
        return parse_money
    raise TypeError(f"no parser for type {parse_type.__name__!r}")
