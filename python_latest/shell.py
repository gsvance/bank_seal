from collections import deque
from typing import Any, Final


WELCOME_MESSAGE: Final[str] = (
    "Welcome to the banking shell!\nType 'help' or another command"
)
SHELL_PROMPT: Final[str] = "$> "


class Shell:

    def __init__(self) -> None:
        self.show_output(WELCOME_MESSAGE)

    def show_output(self, output: Any) -> None:
        string = str(output)
        if string != "":
            print(string, end="\n\n")
        else:
            print()

    def get_words(self) -> deque[str]:
        line = input(SHELL_PROMPT)
        words = split_words(line)
        return words


def split_words(line: str) -> deque[str]:
    # Need to make this better...
    return deque(line.strip().split())
