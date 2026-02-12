from collections import deque
import dataclasses
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


SPACING_MISSING: Final[str] = "shell arguments must be separated by whitespace"
UNCLOSED_QUOTES: Final[str] = "input line ended while parsing quoted argument"
ESCAPED_NEWLINE: Final[str] = "input line cannot end with escape character"


class SplitError(ValueError):
    pass


class SplitState:
    pass


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class BetweenArgs(SplitState):
    seen_space: bool


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class InUnquotedArg(SplitState):
    escaped: bool


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class InSingleQuotedArg(SplitState):
    escaped: bool


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class InDoubleQuotedArg(SplitState):
    escaped: bool


SINGLE_QUOTE: Final[str] = '\''
DOUBLE_QUOTE: Final[str] = '"'
BACKSLASH: Final[str] = '\\'


def split_words(line: str) -> deque[str]:

    args: deque[str] = deque()
    state: SplitState = BetweenArgs(
        seen_space=True,  # Ready to parse first arg immediately
    )

    for character in line:
        match state:

            case BetweenArgs(seen_space=_):
                if character.isspace():
                    state = BetweenArgs(seen_space=True)
                    continue
                if not state.seen_space:
                    raise SplitError(SPACING_MISSING)
                args.append("")
                if character == SINGLE_QUOTE:
                    state = InSingleQuotedArg(escaped=False)
                elif character == DOUBLE_QUOTE:
                    state = InDoubleQuotedArg(escaped=False)
                elif character == BACKSLASH:
                    state = InUnquotedArg(escaped=True)
                else:
                    args[-1] += character
                    state = InUnquotedArg(escaped=False)

            case InUnquotedArg(escaped=_):
                if state.escaped:
                    args[-1] += character
                    state = InUnquotedArg(escaped=False)
                elif character == BACKSLASH:
                    state = InUnquotedArg(escaped=True)
                elif character.isspace():
                    state = BetweenArgs(seen_space=True)
                else:
                    args[-1] += character

            case InSingleQuotedArg(escaped=_):
                if state.escaped:
                    args[-1] += character
                    state = InSingleQuotedArg(escaped=False)
                elif character == BACKSLASH:
                    state = InSingleQuotedArg(escaped=True)
                elif character == SINGLE_QUOTE:
                    state = BetweenArgs(seen_space=False)
                else:
                    args[-1] += character

            case InDoubleQuotedArg(escaped=_):
                if state.escaped:
                    args[-1] += character
                    state = InDoubleQuotedArg(escaped=False)
                elif character == BACKSLASH:
                    state = InDoubleQuotedArg(escaped=True)
                elif character == DOUBLE_QUOTE:
                    state = BetweenArgs(seen_space=False)
                else:
                    args[-1] += character

    match state:
        case InSingleQuotedArg(escaped=_) | InDoubleQuotedArg(escaped=_):
            raise SplitError(UNCLOSED_QUOTES)
        case InUnquotedArg(escaped=_) if state.escaped:
            raise SplitError(ESCAPED_NEWLINE)
        case _:
            return args
