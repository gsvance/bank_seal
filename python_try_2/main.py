#!/usr/bin/env python3

"""Top-level driver code for my personal banking CLI application.

Set the configuration on the command line, and choose whether to give a one-off
command via the command line arguments or to open an interactive terminal where
unlimited numbers of commands can be entered sequentially.

Last modified 25 Sep 2023 by Greg Vance.
"""

import argparse

from data import Data
from terminal import Terminal


def main():

    terminal = Terminal()
    args = parse_command_line_arguments()

    data = Data.load(args.config_name, args.new_config)

    terminal.set_one_off_command(args.command)
    terminal.set_data(data)
    terminal.run()

    data.save()


def parse_command_line_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description="My banking code for personal finances",
    )

    parser.add_argument("config_name", help="name of configuration to load")
    parser.add_argument("-n", "--new_config", action="store_true",
                        help="create new configuration if it doesn't exist")
    parser.add_argument("-c", "--command",
                        help="one-off command to execute from command line")

    return parser.parse_args()


if __name__ == "__main__":
    main()
