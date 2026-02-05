import argparse

from commands import Command
from data import Data
from shell import Shell


def get_command_line_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_name")
    parser.add_argument("-n", "--new_config", action="store_true")
    return parser.parse_args()


def main(config_name: str, new_config: bool) -> None:
    data = Data(config_name, new_config)
    shell = Shell()
    while not data.exiting:
        words = shell.get_words()
        command = Command.create(words)
        reply = command.execute(data)
        shell.show_output(reply)


if __name__ == "__main__":
    command_line_args = get_command_line_args()
    main(
        config_name=command_line_args.config_name,
        new_config=command_line_args.new_config
    )
