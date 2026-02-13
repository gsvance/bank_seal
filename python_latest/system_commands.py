from typing import override

from base_commands import Command
from data import Data
from parameters import declare_parameter


class HelpCommand(Command, identifier="help"):

    @override
    def declare_parameters(self) -> None:
        self.term = declare_parameter("term", str, optional=True)

    @override
    def execute(self, data: Data) -> str:
        if self.term.value is None:
            return "no argument"
        return "argument: " + self.term.value
