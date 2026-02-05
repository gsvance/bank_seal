

import argparse

from commands import ALL_COMMANDS


def main() -> None:
    """Handles command line argument parsing and sub-commands setup."""

    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers()
    for command in ALL_COMMANDS:
        command.create_subparser(subparsers)
    
    args = parser.parse_args()
    chosen_command = args.command(args)
    chosen_command.run()


if __name__ == "__main__":
    main()
