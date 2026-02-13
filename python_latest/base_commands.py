import abc
from collections import deque
from collections.abc import Iterator, Sequence
import typing
from typing import Any, Self

from data import Data
from name import Name
from signature import (
    ArgumentParseError,  declare_parameter, Parameter, ParseMatchMatrix,
)


class CommandRegistryError(Exception):
    """Something went wrong while creating the registry of shell commands."""


class Command(abc.ABC):
    _registry: dict[Name, type[Self]] = {}

    @classmethod
    def __init_subclass__(cls, /, identifier: str | None, **kwargs) -> None:
        """This special method is called every time a subclass is defined.

        Specifically, each time a new class is defined that inherits from
        Command, Python will execute the class definition and then call this
        method immediately after. The newly created class object (the subclass
        of Command) is passed via the cls parameter. Note that this method is
        still executed in the context of the Command class, not the subclass,
        so super() refers to the parent class of Command, which is object.

        Here, this method adds the new subclass to the command registry with a
        unique identifier string for use with the shell. The identifier string
        should either be a valid name, or be set explicitly to None to exclude
        the new command from the registry.
        """
        # Call the same method for object. This *should* do nothing, but will
        # throw an exception if there are any extra keyword arguments.
        super().__init_subclass__(**kwargs)

        name = None if identifier is None else Name(identifier)
        cls.IDENTIFIER: Name | None = name

        # Register the new subclass as an available shell command unless its
        # identifier was None. Note that Command and its subclass are able to
        # share the same class attribute. The registry dict exists on both and
        # it always refers to the same object with the same id.
        if name is not None:
            if name in cls._registry:
                raise CommandRegistryError(
                    f"two commands defined with same identifier {name!r}"
                )
            cls._registry[name] = cls

    # Note: this class method needs to have a return type of Command (instead
    # of Self) because it returns subclass instances rather than instances of
    # *this* class specifically
    @classmethod
    def create(cls, words: deque[str]) -> 'Command':
        try:
            identifier = words.popleft()
        except IndexError:
            return NothingCommand([])

        try:
            name = Name(identifier)
            command_subclass = cls._registry[name]
        except (ValueError, KeyError):
            return UnknownCommand([identifier])

        args = words
        try:
            return command_subclass(args)
        except ArgumentParseError as e:
            return ArgumentErrorCommand(e.args)

    @abc.abstractmethod
    def declare_parameters(self) -> None:
        ...

    def iter_parameters(self) -> Iterator[tuple[str, Parameter]]:
        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)
            if isinstance(attribute, Parameter):
                yield attribute_name, attribute

    @property
    def min_args(self) -> int:
        return sum(
            1 for _, parameter in self.iter_parameters()
            if not parameter.optional
        )

    @property
    def max_args(self) -> int:
        return sum(1 for _ in self.iter_parameters())

    def __init__(self, args: Sequence[str]) -> None:
        # Let the subclass declare its parameters as instance attributes
        self.declare_parameters()

        # Detect the declared parameters using introspection and validate them
        parameters: dict[str, Parameter] = {}
        for attribute_name, parameter in self.iter_parameters():
            for other_parameter in parameters.values():
                other_parameter.check_for_obvious_conflicts(parameter)
            parameters[attribute_name] = parameter

        # Make sure the arguments make sense
        if len(args) < self.min_args:
            raise ArgumentParseError(
                f"this command requires at least {self.min_args} arguments(s)"
            )
        if len(args) > self.max_args:
            raise ArgumentParseError(
                f"this command accepts at most {self.max_args} argument(s)"
            )

        # Parse the arguments by matching them against the parameters
        matrix = ParseMatchMatrix(args, list(parameters.values()))
        while not matrix.is_empty():
            parsed_argument, matched_parameter = matrix.pop_match()
            matched_parameter.parsed_value = parsed_argument

    @abc.abstractmethod
    def execute(self, data: Data) -> Any:
        ...


class NothingCommand(Command, identifier=None):

    @typing.override
    def declare_parameters(self) -> None:
        pass

    @typing.override
    def execute(self, data: Data) -> str:
        return ""


class UnknownCommand(Command, identifier=None):

    @typing.override
    def declare_parameters(self) -> None:
        self.unknown_identifier = declare_parameter('unknown_identifier', str)

    @typing.override
    def execute(self, data: Data) -> str:
        return f"unknown command: {self.unknown_identifier.value!r}"


class ArgumentErrorCommand(Command, identifier=None):

    @typing.override
    def declare_parameters(self) -> None:
        self.error_message = declare_parameter('error_message', str)

    @typing.override
    def execute(self, data: Data) -> Any:
        return f"argument error: {self.error_message.value!s}"
