from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class Parameter(Generic[T]):
    # Proposed attributes...
    name: Name  # or Name
    optional: bool  # or required, or part of subclass type info
    parser: Parser[T]
    indices: frozenset[int]  # or special ParameterIndices dataclass
    _value: T  # or Union[T, None, UNSET]


# How do I make Parameter hashable if it needs a value attribute that needs to
# be mutated? Should I make a hashable object with most of the attributes that
# lives inside Parameter? ParameterSpec? Does Parameter need to be hashable to
# make the ParseMatrix work? Could it work any differently?

# Another detail: if a Parameter is optional (not required) then the type T of
# the value needs to change from T to Union[T, None]. Maybe there could be two
# methods/properties with return types T and Union[T, None] for required and
# optional Parameters. Or maybe I could have two subclasses: RequiredParameter
# and OptionalParameter. That way, the required or optional boolean is being
# tracked by the type system rather than by a boolean attribute.

# Put parser and indices in their own hashable spec class, let name be
# external, and use subclasses to encode the optional/required info. The
# subclasses can also handle the _value in their own two ways.
