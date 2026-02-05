"""Deets

Last modified 13 May 2023 by Greg Vance.
"""


def encypher(s: str) -> bytes:
    return s.encode()


def decypher(b: bytes) -> str:
    return b.decode()
