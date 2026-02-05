"""A bare-bones mimickry of Rust's Result<T, E> type in Python.

Last modified 13 Nov 2023 by Greg Vance.
"""


from typing import Generic, NoReturn, TypeAlias, TypeVar, Union


S = TypeVar('S', covariant=True)
F = TypeVar('F', covariant=True)


class Success(Generic[S]):

    __slots__ = ("_value",)

    def __init__(self, value: S) -> None:
        self._value = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    def is_good(self) -> bool:
        return True

    def is_bad(self) -> bool:
        return False

    def grab(self) -> S:
        return self._value

    def grab_error(self) -> NoReturn:
        raise RuntimeError("called prob() method on {self!r}")


class Failure(Generic[F]):

    __slots__ = ("_error",)

    def __init__(self, error: F) -> None:
        self._error = error

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._error!r})"

    def is_good(self) -> bool:
        return False

    def is_bad(self) -> bool:
        return True

    def grab(self) -> NoReturn:
        raise RuntimeError(f"called grab() method on {self!r}")

    def grab_error(self) -> F:
        return self._error


Outcome: TypeAlias = Union[Success[S], Failure[F]]
