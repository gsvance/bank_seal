"""A collection of parser functions to be used with command signatures.

A parser (indicated by the generic Parser[T] type alias) is any callable that
takes a string and returns a type T on success or None on failure.
"""

from typing import Callable, Final, TypeAlias, TypeVar

from name import Name


T = TypeVar('T')
Parser: TypeAlias = Callable[[str], T | None]


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


'''def parse_date(s: str) -> 'Date | None':
    pass'''


'''def parse_money(s: str) -> 'Money | None':
    pass'''


'''def parse_merchant(s: str) -> 'Merchant | None':
    pass'''


'''def parse_transaction(s: str) -> 'Transaction | None':
    pass'''


def get_parser(parse_type: type[T]) -> Parser[T]:
    if parse_type is str:
        return parse_str
    if parse_type is Name:
        return parse_name
    if parse_type is int:
        return parse_int
    raise TypeError(f"no parser for type {parse_type.__name__!r}")
