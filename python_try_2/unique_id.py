"""Tools to generate randomized hex values for use as unique IDs.

Last modified 14 Oct 2023 by Greg Vance.
"""

import random
from typing import Container, NewType


_BITS_PER_HEX_DIGIT = 4  # because 2 ** 4 == 16

UniqueID = NewType("UniqueID", int)
HexID = NewType("HexID", str)


def generate_new_unique_id(
    n_hex_digits: int,
    existing_ids: Container[UniqueID] | None = None
) -> UniqueID:
    """Generate a unique ID using the given number of hex digits.

    If provided, the existing_ids container is a collection of UniqueIDs that
    *will not* be returned by this function.
    """
    if n_hex_digits < 1:
        raise ValueError("n_hex_digits = {n_hex_digits} is less than one")
    if existing_ids is None:
        existing_ids = set()

    n_bits = n_hex_digits * _BITS_PER_HEX_DIGIT
    new_id = UniqueID(_generate_random_binary(n_bits))
    while new_id in existing_ids:
        new_id = UniqueID(_generate_random_binary(n_bits))
    return new_id


def _generate_random_binary(n_bits: int) -> int:
    """Generate a pseudo-random unsigned int with the given number of bits."""
    if n_bits < 0:
        raise ValueError(f"n_bits = {n_bits} is less than zero")

    largest_value = 2 ** n_bits - 1
    return random.randint(0, largest_value)


def id_to_hex(unique_id: UniqueID, width: int) -> HexID:
    """Format a unique ID as a hex string zero-padded to a specific width."""
    if width < 0:
        raise ValueError(f"width value {width} is less than zero")
    hex_str = f"{unique_id:x}".zfill(width)
    if len(hex_str) > width:
        raise ValueError(f"provided unique ID {unique_id} is too wide")
    return HexID(hex_str)


def hex_to_id(hex_id: HexID) -> UniqueID:
    """Parse a hex string to a numeric unique ID integer."""
    return UniqueID(int(hex_id, base=16))
