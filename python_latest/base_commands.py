from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Sequence
from typing import Any

from data import Data
from name import Name
from parsers import parse_str
from signature import ArgumentParseError, Signature


class CommandRegistryError(Exception):
    """Something went wrong while creating the registry of shell commands."""


class Command(ABC):
    _registry: dict[Name, type['Command']] = {}

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
        the new command from the registry. This method also forces the new
        subclass to generate its parameter signature.
        """
        # Call the same method for object. This *should* do nothing, but will
        # throw an exception if there are any extra keyword arguments.
        super().__init_subclass__(**kwargs)

        name = None if identifier is None else Name(identifier)
        cls.IDENTIFIER = name

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

        # Force the new subclass to generate and save its signature now. This
        # could be done lazily the first time the command is invoked, but that
        # might add a weird delay and it would be more complicated to code up.
        # An advantage of this strategy is that it forces any signature errors
        # to happen on program startup instead of waiting until the user calls
        # the broken command.
        #cls.SIGNATURE = cls.generate_signature()

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

    def __init__(self, args: Sequence[str]) -> None:
        # Let the subclass declare its parameters as instance attriibutes
        self.declare_parameters()

        # Detect the declared parameters using introspection and validate them
        parameters = {}
        for attribute_name, attribute in self.__dict__.items():
            if not isinstance(attribute, Parameter):
                continue
            for parameter in parameters.values():
                parameter.check_for_obvious_conflicts(attribute)
            parameters[attribute_name] = attribute
            setattr(self, attribute_name, None)

        # Parse the arguments by matching them against the parameters
        matrix = ParseMatchMatrix(args, parameters)
        while matrix.is_not_empty():
            parsed_arg, matched_param = matrix.pop_match()
            setattr(self, matched_param, parsed_arg)

    @abstractmethod
    def declare_parameters(self) -> None:
        ...

    def parse_arguments(args: Sequence[str]) -> None:
        pass

    @abstractmethod
    def execute(self, data: Data) -> Any:
        ...-


class NothingCommand(Command, identifier=None):

    def declare_parameters(self) -> None:
        pass

    def execute(self, data: Data) -> str:
        return ""


class UnknownCommand(Command, identifier=None):

    def declare_parameters(self) -> None:
        self.unknown_identifier = declare_parameter(str)

    def execute(self, data: Data) -> str:
        return f"unknown command: {self.unknown_identifier!r}"


class ArgumentErrorCommand(Command, identifier=None):

    def declare_parameters(self) -> None:
        self.error_message = declare_parameter(str)

    def execute(self, data: Data) -> Any:
        return f"argument error: {self.error_message!s}"
