

import argparse


Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]


class Command:

    @classmethod
    def create_subparser(cls, subparsers: Subparsers) -> None:
        name = cls.__name__.lower()
        subparser = subparsers.add_parser(name, help=f"{name} help")

    def __init__(self, args: argparse.Namespace):
        self.args = args
    
    def run(self) -> None:
        raise NotImplementedError()


class Add(Command):
    """Create a new transation and add it to the record."""
    pass


class Print(Command):
    """Print a selection of the recorded transactions."""
    pass


class Search(Command):
    """Search for transactions meeting certain criteria."""
    pass


class Delete(Command):
    """Delete a transaction from the record."""
    pass


class Edit(Command):
    """Make changes to a previously recorded transaction."""
    pass


class Report(Command):
    """Generate a statement for a range of transactions."""
    pass


class Categorize(Command):
    """Fit transations into categories."""
    pass


class Construct(Command):
    """Construct a new merchant for the records."""
    pass


class Demolish(Command):
    """Destroy a recorded merchant."""
    pass


class Remodel(Command):
    """Edit an exisitng merchant."""
    pass


ALL_COMMANDS = Command.__subclasses__()
