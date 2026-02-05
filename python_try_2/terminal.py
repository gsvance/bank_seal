"""Terminal class for running the main loop and handling input/output.

All output from and input to this program are hereby restricted to using the
associated methods on this class.

Last modified 25 Sep 2023 by Greg Vance.
"""

from typing import Iterable

try:
    import readline
except ImportError:
    readline = None

from command import Command
from data import Data


_PROMPT_STRING = ">>> "


class Terminal:

    def __init__(self) -> None:
        self.one_off_command = None
        self.data = None
        self.exit = False
        self.send_output(self.welcome)

    @property
    def readline_status(self) -> str:
        if readline is not None:
            return "Successfully imported readline module for this platform."
        else:
            return "No importable readline module was found on this platform."

    @property
    def welcome(self) -> str:
        return '\n'.join([
            "Generic welcome message!",
            self.readline_status,
        ])

    def set_one_off_command(self, one_off_command: str | None) -> None:
        self.one_off_command = one_off_command

    def set_data(self, data: Data) -> None:
        self.data = data

    def take_input(self) -> str:
        return input(_PROMPT_STRING)

    def send_output(self, text: str) -> None:
        print(text, end="\n\n")

    def iter_inputs(self) -> Iterable[str]:
        if self.one_off_command is None:
            while not self.exit:
                yield self.take_input()
        else:
            yield self.one_off_command
            self.exit = True

    def run(self) -> None:
        assert self.data is not None
        for input_text in self.iter_inputs():
            command = Command.interpret(input_text)
            self.send_output(command.execute(self.data))
            self.exit = command.is_exit()
