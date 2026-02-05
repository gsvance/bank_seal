from base_commands import Command
from data import Data
from parsers import parse_str
from signature import Signature


class HelpCommand(Command, identifier="help"):

    @classmethod
    def generate_signature(cls) -> Signature:
        sig = Signature()
        sig.add_parameter("term", parse_str, optional=True)
        return sig

    def execute(self, data: Data) -> str:
        if self.term is None:
            return "no argument"
        return "argument: " + self.term
