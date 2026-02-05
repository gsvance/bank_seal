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

# from collections.abc import Iterable, Sequence
# from dataclasses import dataclass
# from typing import Any, Final, Generic, TypeVar

# from name import Name
# from parsers import Parser


# T = TypeVar('T')

# EMPTY_SET: Final[frozenset] = frozenset()


'''class SignatureBuildError(Exception):
    """A logical failure occurred in the process of building a signature."""
'''


'''class ArgumentParseError(Exception):
    """A signature was not able to unambiguously parse the given arguments."""
'''


'''@dataclass(frozen=True, slots=True)
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

    def overlaps_with(self, other: 'ParameterIndices') -> bool:
        """Return whether two index sets overlap anywhere.

        This is basically just a set intersection check, but we also have to
        remember that None represents a set containing all possible indices.
        """
        if self.indices is None or other.indices is None:
            return True
        return self.indices & other.indices != EMPTY_SET

    def __contains__(self, index: int) -> bool:
        """Return whether a given index is in the index set.

        If the indices attribute is None then it contains all indices.
        """
        if self.indices is None:
            return True
        return index in self.indices
'''


'''@dataclass(frozen=True, slots=True)
class Parameter(Generic[T]):
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

    def check_for_obvious_conflicts(self, other: 'Parameter') -> None:
        """Raise an error if two parameters conflict in some obvious way."""
        if other.name == self.name:
            raise SignatureBuildError(
                f"parameter name {other.name!r} is a duplicate"
            )
        if not other.indices.overlaps_with(self.indices):
            return  # Non-overlapping positional arguments
        if other.optional != self.optional:
            return  # One is optional and the other is required
        if other.parser != self.parser:
            return  # Looking for different types
        raise SignatureBuildError('\n'.join([
            "apparent parameter conflict detected:", repr(other), repr(self)
        ]))

    def parse(self, index: int, s: str) -> T | None:
        if index not in self.indices:
            return None
        return self.parser(s)
'''


'''class Signature:

    def __init__(self) -> None:
        self.params: list[Parameter] = []

    def add_parameter(
        self,
        name: str,
        parser: Parser[T],
        indices: Iterable[int] | None = None,
        optional: bool = False,
    ) -> None:

        valid_name = Name(name)
        valid_indices = ParameterIndices(
            None if indices is None else frozenset(indices)
        )
        new_param = Parameter(valid_name, parser, valid_indices, optional)
        for param in self.params:
            param.check_for_obvious_conflicts(new_param)
        self.params.append(new_param)

    @property
    def min_args(self) -> int:
        return sum(
            1 for param in self.params if not param.optional
        )

    @property
    def max_args(self) -> int:
        return len(self.params)

    def parse_arguments(
        self,
        args: Sequence[str]
    ) -> dict:
        n_args = len(args)
        if n_args < self.min_args:
            raise ArgumentParseError(
                f"this command requires at least {self.min_args} arguments(s)"
            )
        if n_args > self.max_args:
            raise ArgumentParseError(
                f"this command accepts at most {self.max_args} argument(s)"
            )
        matrix = ParseMatchMatrix(args, self.params)
        results = {param: None for param in self.params if param.optional}
        while matrix.is_not_empty():
            parsed_arg, matched_param = matrix.pop_match()
            results[matched_param] = parsed_arg
        return results
'''


'''class ParseMatchMatrix:

    def __init__(
        self,
        args: Sequence[str],
        params: Sequence[Parameter],
    ) -> None:

        self.matrix: dict[tuple[int, str], dict[Parameter, Any]] = {}
        for i_arg, arg in enumerate(args):
            self.matrix[i_arg, arg] = {
                param: param.parse(i_arg, arg) for param in params
            }

        # Check columns to ensure all required params have something
        for param in params:
            possibilities = 0
            for i_arg, arg in self.matrix:
                if self.matrix[i_arg, arg][param] is not None:
                    possibilities += 1
            if possibilities == 0 and not param.optional:
                raise ArgumentParseError(
                    f"no argument matches required parameter {param.name!r}"
                )

    def is_not_empty(self) -> bool:
        return len(self.matrix) > 0

    def pop_match(self) -> tuple[T, Parameter[T]]:
        for i_arg, arg in self.matrix:
            row_results = self.condense_row(i_arg, arg)
            if len(row_results) == 0:
                raise ArgumentParseError(
                    f"argument {arg!r} matches no parameters"
                )
            if len(row_results) == 1:
                matched_param, parsed_arg = list(row_results.items())[0]
                self.remove_arg(i_arg, arg)
                self.remove_param(matched_param)
                return parsed_arg, matched_param
        raise ArgumentParseError(
            f"failed to match argument {list(self.matrix.keys())[0][1]!r}"
        )

    def condense_row(self, i_arg: int, arg: str) -> dict[Parameter[T], T]:
        return {
            param: parsed_arg
            for param, parsed_arg in self.matrix[i_arg, arg].items()
            if parsed_arg is not None
        }

    def remove_arg(self, i_arg: int, arg: str) -> None:
        del self.matrix[i_arg, arg]

    def remove_param(self, param: Parameter) -> None:
        for row in self.matrix.values():
            del row[param]
'''



