from collections.abc import Iterator
from dataclasses import dataclass
import math
import random
import struct
from typing import Final, Generic, TypeVar


T = TypeVar('T')


# Isolate the internal bytes format for HexID in case I want to change it
HEX_INT_FORMAT: Final[str] = '!I'  # Network-standard unsigned int (32-bit)

HEX_BASE: Final[int] = 16
HEX_DIGIT_BITS: Final[int] = round(math.log(HEX_BASE, 2))

HEX_ID_BITS: Final[int] = 8 * len(struct.pack(HEX_INT_FORMAT, 0))
HEX_ID_DIGITS: Final[int] = math.ceil(HEX_ID_BITS / HEX_DIGIT_BITS)

HEX_ID_VALUES: Final[int] = 2 ** HEX_ID_BITS

HEX_ID_NUDGE: Final[int] = 91  # Any number with no factors of 2

HEX_STR_FORMAT = ''.join(['{:0', str(HEX_ID_DIGITS), 'x}'])


@dataclass(order=True, frozen=True, slots=True)
class HexID:
    hex_int: bytes

    @classmethod
    def from_int(cls, i: int) -> 'HexID':
        return cls(struct.pack(HEX_INT_FORMAT, i % HEX_ID_VALUES))

    @classmethod
    def random(cls) -> 'HexID':
        return cls.from_int(random.randrange(HEX_ID_VALUES))

    @classmethod
    def from_str(cls, s: str) -> 'HexID':
        return cls.from_int(int(s, base=HEX_BASE))

    def __int__(self) -> int:
        i, = struct.unpack(HEX_INT_FORMAT, self.hex_int)
        return i

    def nudge(self) -> 'HexID':
        next_int = int(self) + HEX_ID_NUDGE
        return self.__class__.from_int(next_int)

    def __str__(self) -> str:
        return HEX_STR_FORMAT.format(int(self))

    def __repr__(self) -> str:
        return f"HexID(0x{self!s})"


class HexIDSpace(Generic[T]):

    def __init__(self) -> None:
        self.map: dict[HexID, T] = {}

    def __len__(self) -> int:
        return len(self.map)

    def generate_id(self) -> HexID:
        if len(self) == HEX_ID_VALUES:
            raise RuntimeError("a hex id space has grown to maximum size")
        hex_id = HexID.random()
        while hex_id in self.map:
            hex_id = hex_id.nudge()
        return hex_id

    def deposit(self, value: T) -> HexID:
        hex_id = self.generate_id()
        self.map[hex_id] = value
        return hex_id

    def lookup(self, hex_id: HexID) -> T | None:
        return self.map.get(hex_id)

    def withdraw(self, hex_id: HexID) -> T | None:
        try:
            value = self.map[hex_id]
        except KeyError:
            return None
        del self.map[hex_id]
        return value

    def __iter__(self) -> Iterator[tuple[HexID, T]]:
        return iter(self.map.items())

    def ids(self) -> Iterator[HexID]:
        return iter(self.map.keys())
