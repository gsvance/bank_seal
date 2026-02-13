"""Data structures for representing the parameter signatures of commands.

The system implemented here is a nonstandard one that's more flexible than the
typical Linux/Unix terminal command syntax. It doesn't have any flags and also
relies minimally on the ordering of positional arguments. Instead, arguments
are identified primarily by their types, which are determined by whether an
associated parser function succeeds in parsing the provided string.

For example, a command that requires a date, a dollar amount, and a merchant
identifier can use a signature that accepts those three arguments in *any*
order. As long as the user provides the correct number of arguments, then the
date is just whichever one successfully parses as a date, the dollar amount is
the one that parses as a dollar amount, and the merchant identifier is the one
for which the merchant lookup operation doesn't fail.

The general idea is to create a friendly interface that doesn't require the
user to memorize the order of positional arguments for each command or employ a
metric ton of clunky tags. The downside is the potential for ambiguous calls,
but the associated risks can be mitigated with strict validation logic and a
refusal to execute any command when its parameters cannot be unambiguously
identified.

When needed, parameters *can* be made strictly or loosely positional using a
system of index sets. A parameter with indices of {1, 2} must appear as either
the second or the third argument, and one with indices of {0} must always be
the first argument. Parameters can also be optional, meaning that no argument
which parses appropriately is required to appear.
"""

from collections.abc import Iterable
import dataclasses
import itertools
from typing import Any, Final, Self

from name import Name
from parsers import Parser, get_parser


EMPTY_SET: Final[frozenset[int]] = frozenset()


class SignatureBuildError(Exception):
    """A logical failure occurred in the process of building a signature."""


class ArgumentParseError(Exception):
    """A signature was not able to unambiguously parse the given arguments."""


@dataclasses.dataclass(frozen=True, match_args=False, slots=True)
class ParameterIndices:
    """A set of nonnegative positional indices where a parameter might appear.

    A value of None for the indices attribue indicates that all positional
    indices are allowed. Parameters must have at least one allowed index.
    """
    indices: frozenset[int] | None

    def __post_init__(self) -> None:
        """Validate the newly initialized index set."""
        if self.indices is None:
            return
        if self.indices == EMPTY_SET:
            raise SignatureBuildError(
                "parameter indices must include at least one allowed index"
            )
        for index in self.indices:
            if index < 0:
                raise SignatureBuildError(
                    "negative parameter indices are not supported"
                )

    def overlaps_with(self, other: Self) -> bool:
        """Return whether two index sets overlap anywhere.

        This is basically just a set intersection check, but we also have to
        remember that None represents a set containing all possible indices.
        """
        if self.indices is None or other.indices is None:
            return True
        return self.indices & other.indices != EMPTY_SET

    def __contains__(self, index: int) -> bool:
        """Return whether a given index is in the index set.

        If the indices attribute is None, then it contains all non-negative
        indices.
        """
        if index < 0:
            return False
        if self.indices is None:
            return True
        return index in self.indices


class UnsetType:
    pass


UNSET: Final[UnsetType] = UnsetType()


@dataclasses.dataclass(match_args=False, slots=True)
class Parameter[T]:
    """A single expected parameter for a command's signature.

    The parameter has a unique name to identify it, a parser function that
    converts the input string to the desired type, a set of possible positional
    indices where the parameter might be found within the argument list, and a
    flag to specify whether it is required or optional.
    """
    name: Name
    parser: Parser[T]
    indices: ParameterIndices
    optional: bool
    _value: (T | None) | UnsetType

    def check_for_obvious_conflicts(self, other: Self) -> None:
        """Raise an error if two parameters conflict in some obvious way."""
        if other.name == self.name:
            raise SignatureBuildError(
                f"parameter name {other.name!r} is a duplicate"
            )
        if not other.indices.overlaps_with(self.indices):
            return  # Non-overlapping positional arguments
        if other.optional != self.optional:
            return  # One is optional and the other is required
        if other.parser is not self.parser:
            return  # Looking for different types
        raise SignatureBuildError('\n'.join([
            "apparent parameter conflict detected:", repr(other), repr(self)
        ]))

    def parse(self, index: int, s: str) -> T | None:
        if index not in self.indices:
            return None
        return self.parser(s)

    def set_value(self, value: T | None) -> None:
        if value is None and not self.optional:
            raise ValueError("non-optional parameter cannot be set to None")
        self._value = value

    @property
    def value(self) -> T | None:
        if isinstance(self._value, UnsetType):
            raise ValueError("retrieving value from an unset parameter")
        return self._value


def declare_parameter[T](
    name: str,
    type_: type[T],
    indices: Iterable[int] | None = None,
    optional: bool = False,
) -> Parameter[T]:
    name_object = Name(name)
    parser_function = get_parser(type_)
    indices_object = ParameterIndices(
        None if indices is None else frozenset(indices)
    )
    start_value = None if optional else UNSET

    return Parameter(
        name=name_object,
        parser=parser_function,
        indices=indices_object,
        optional=optional,
        _value=start_value,
    )


type EnumeratedList[E] = list[tuple[int, E]]


def fetch_from_enumerated_list[T](
    enumerated_list: EnumeratedList[T], i: int,
) -> T:
    for i_value, value in enumerated_list:
        if i_value == i:
            return value
    raise IndexError("no pair was found with i = {i}")


def remove_from_enumerated_list[T](
    enumerated_list: EnumeratedList[T], i: int,
) -> None:
    for true_index, (i_value, _value) in enumerate(enumerated_list):
        if i_value == i:
            del enumerated_list[true_index]
            return
    raise ValueError(f"no pair was found with i = {i}")


class ParseMatchMatrix:

    def __init__(self, args: list[str], params: list[Parameter]) -> None:
        # Copy the args and params and then enumerate both
        self.args: EnumeratedList[str] = list(enumerate(args[:]))
        self.params: EnumeratedList[Parameter] = list(enumerate(params[:]))

        self.matrix: dict[tuple[int, int], Any] = {}
        for i_arg, arg in self.args:
            for i_param, param in self.params:
                self.matrix[i_arg, i_param] = param.parse(i_arg, arg)

        # Check columns to ensure all required params have something
        for i_param, param in self.params:
            possibilities = 0
            for i_arg, arg in self.args:
                if self.matrix[i_arg, i_param] is not None:
                    possibilities += 1
            if possibilities == 0 and not param.optional:
                raise ArgumentParseError(
                    f"no argument matches required parameter {param.name!r}"
                )

    def is_empty(self) -> bool:
        return len(self.matrix) == 0

    def pop_match[T](self) -> tuple[T, Parameter[T]]:
        for i_arg, arg in self.args:
            row_results = self.condense_row(i_arg)
            if len(row_results) == 0:
                raise ArgumentParseError(
                    f"argument {arg!r} matches no parameters"
                )
            if len(row_results) == 1:
                i_param, parsed_arg = row_results.popitem()
                param = fetch_from_enumerated_list(self.params, i_param)
                self.remove_arg(i_arg)
                self.remove_param(i_param)
                return parsed_arg, param

        _i_arg, arg = self.args.pop(0)
        raise ArgumentParseError(f"failed to match argument {arg!r}")

    def condense_row(self, i_arg: int) -> dict[int, Any]:
        row_results: dict[int, Any] = {}
        for i_param, _param in self.params:
            parsed_arg = self.matrix[i_arg, i_param]
            if parsed_arg is not None:
                row_results[i_param] = parsed_arg
        return row_results

    def remove_arg(self, i_arg: int) -> None:
        for i_param, _param in self.params:
            del self.matrix[i_arg, i_param]
        remove_from_enumerated_list(self.args, i_arg)

    def remove_param(self, i_param: int) -> None:
        for i_arg, _arg in self.args:
            del self.matrix[i_arg, i_param]
        remove_from_enumerated_list(self.params, i_param)


def parse_arguments(args: list[str], params: list[Parameter]) -> None:
    # Check for obvious conflicts between parameters
    for param_1, param_2 in itertools.combinations(params, 2):
        param_1.check_for_obvious_conflicts(param_2)

    # Count the minimum and maximum numbers of acceptable args
    min_args, max_args = 0, 0
    for param in params:
        max_args += 1
        if not param.optional:
            min_args += 1

    # Make sure the arguments make sense
    if len(args) < min_args:
        raise ArgumentParseError(
            f"this command requires at least {min_args} arguments(s)"
        )
    if len(args) > max_args:
        raise ArgumentParseError(
            f"this command accepts at most {max_args} argument(s)"
        )

    # Parse the arguments by matching them against the parameters
    matrix = ParseMatchMatrix(args, params)
    while not matrix.is_empty():
        parsed_arg, matched_param = matrix.pop_match()
        matched_param.set_value(parsed_arg)
