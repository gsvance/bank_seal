"""Interface for parsing user terminal commands and their arguments.

This class only parses commands and maps them to the appropriate executable
functions. The actual legwork is done by those executable functions.

Last modified 25 Sep 2023 by Greg Vance.
"""

import shlex
from typing import List

from data import Data
from executables import find_executable, get_exit_reference


class Command:

    def __init__(self, command_name: str, command_args: List[str]) -> None:
        self.name = command_name
        self.args = command_args.copy()
        self.executable = find_executable(self.name)

    @classmethod
    def interpret(cls, shell_input: str) -> 'Command':
        shell_args = _shell_split(shell_input)
        command_name = shell_args[0] if len(shell_args) > 0 else ""
        command_args = shell_args[1:] if len(shell_args) > 1 else list()
        return Command(command_name, command_args)

    def execute(self, data: Data) -> str:
        return self.executable(self.args, data)

    def is_exit(self) -> bool:
        return self.executable is get_exit_reference()


def _shell_split(shell_string: str) -> List[str]:
    """Split a continuous string of shell words into a list of strings."""
    return shlex.split(shell_string)
