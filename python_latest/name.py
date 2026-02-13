"""Contains a dataclass for pedantically validated "name" strings."""

import dataclasses
import string
from typing import Final


ASCII_LETTERS: Final[frozenset[str]] = frozenset(string.ascii_letters)
ASCII_DIGITS: Final[frozenset[str]] = frozenset(string.digits)
VALID_CHARACTERS: Final[frozenset[str]] = (
    ASCII_LETTERS | ASCII_DIGITS | frozenset('_')
)


@dataclasses.dataclass(repr=False, frozen=True, match_args=False, slots=True)
class Name:
    """Names are a limited subset of all strings subject to validation logic.

    A valid name is a non-empty string that begins with an ASCII letter and
    contains only ASCII letters, ASCII digits, and underscores. Anything that
    passes validation should be generally safe to use as a Python identifier
    or to include as part of a file name.
    """
    name: str

    def __post_init__(self) -> None:
        if self.name == "":
            raise ValueError("name string cannot be empty")
        if self.name[0] not in ASCII_LETTERS:
            raise ValueError("name string must begin with an ASCII letter")
        for char in self.name[1:]:
            if char not in VALID_CHARACTERS:
                raise ValueError(
                    f"name string contains invalid character {char!r}"
                )

    def __repr__(self) -> str:
        return repr(self.name)

    def __str__(self) -> str:
        return self.name
