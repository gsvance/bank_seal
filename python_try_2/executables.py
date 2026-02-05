"""Substantial functions corresponding with the available terminal commands.

The functions in the bulk of this file handle the legwork of the operations
requested by the user. Parsing of terminal commands is handled by the Command
class.

Last modified 25 Sep 2023 by Greg Vance.
"""

import os.path
from typing import Any, Callable, Dict, List

from data import Data
from date import Date
from merchants import MERCHANT_ID_SIZE
from money import Money
from table import format_as_table
from transaction import Transaction
from unique_id import id_to_hex


# Official type of all "executable functions"
# These functions correspond to terminal commands for the user
Args = List[str]
Executable = Callable[[Args, Data], str]

# Mapping from terminal command names to corresponding Python functions
_EXECUTABLE_REGISTRY: Dict[str, Executable] = dict()


def register_executable(name: str) -> Callable[[Executable], Executable]:
    """Register the decorated executable function in the global registry."""

    # Note: *this* is how you make decorators take arguments such as 'name'
    # You have to make an *outer* decorator that returns an *inner* decorator
    def inner_decorator(executable: Executable) -> Executable:
        if name in _EXECUTABLE_REGISTRY:
            raise ValueError(f"{name!r} was registered twice as an executable")
        _EXECUTABLE_REGISTRY[name] = executable
        return executable

    return inner_decorator


def find_executable(name: str) -> Executable:
    """Return a reference to the function associated with a command name."""
    try:
        return _EXECUTABLE_REGISTRY[name]
    except KeyError:
        raise ValueError(f"cannot find executable with name {name!r}")
        # TODO: change this to return a nice fallback 'error' function


def get_exit_reference() -> Executable:
    """Return a reference to the function that should exit the program."""
    return exit_program


def preprocess_args(args: Args, converters: List[Callable]) -> List[Any]:
    """"""
    if len(args) != len(converters):
        raise TypeError(
            f"expected {len(converters)} args but got {len(args)} instead"
        )
        # TODO: change the fact that this case crashes the program
    results = list()
    for arg, converter in zip(args, converters):
        results.append(converter(arg))
    return results


# SYSTEM

@register_executable("exit")
def exit_program(args: Args, data: Data) -> str:
    """exit"""
    args = preprocess_args(args, [])
    return "Exiting..."


@register_executable("help")
def provide_help(args: Args, data: Data) -> str:
    """help"""
    args = preprocess_args(args, [])
    return "Helping..."


@register_executable("save")
def save_data_to_files(args: List[str], data: Data) -> str:
    """Save the Ledger and Merchants data to disk so it isn't lost."""
    args = preprocess_args(args, [])
    data.save(save_config_too=False)
    ledger_file_name = os.path.basename(data.config.get_ledger_path())
    merchants_file_name = os.path.basename(data.config.get_merchants_path())
    return '\n'.join([
        f"Ledger was saved to {ledger_file_name}",
        f"Merchants were saved to {merchants_file_name}",
    ])


# CONFIGURATION

@register_executable("conf")
def modify_configuration(args: List[str], data: Data) -> str:
    """config"""
    if len(args) < 2:
        processed_args = preprocess_args(args, [str])
        processed_args.append(None)
    else:
        processed_args = preprocess_args(args, [str, str])

    key, value = processed_args
    output_lines = list()

    current_value = data.config.read(key)
    output_lines.append(f"reading: config[{key!r}] = {current_value!r}")

    if value is not None:
        data.config.write(key, value)
        output_lines.append(f"writing: config[{key!r}] = {value!r}")
        data.config.save()

    return '\n'.join(output_lines)


# TRANSACTIONS

@register_executable("add")
def add_new_transaction(args: List[str], data: Data) -> str:
    """Create a new transation and add it to the ledger."""
    if len(args) > 3:
        processed_args = preprocess_args(
            args, [Date.parse, str, Money.parse, str]
        )
    else:
        processed_args = preprocess_args(args, [Date.parse, str, Money.parse])
        processed_args.append("")

    date, merchant_name, amount, note = processed_args
    merchant_id = data.merchants.get_merchant_id(merchant_name)
    transaction = Transaction(date, merchant_id, amount, note=note)
    data.ledger.insert_transaction(transaction)

    return f"inserting transaction:\n{transaction}"


@register_executable("recent")
def print_recent_transactions(args: List[str], data: Data) -> str:
    """Print a selection of the recorded transactions."""
    if len(args) > 1:
        processed_args = preprocess_args(args, [int])
    else:
        processed_args = [10]
    n_newest, = processed_args
    transactions = data.ledger.find_newest_transactions(n_newest)
    transaction_ids = [t.transaction_id for t in transactions]
    dates = [t.date for t in transactions]
    merchants = [
        data.merchants.get_merchant_full_name(merchant_id)
        for merchant_id in [t.merchant_id for t in transactions]
    ]
    amounts = [t.amount for t in transactions]
    notes = [t.note for t in transactions]

    columns = [transaction_ids, dates, merchants, amounts]
    column_names = ["ID", "Date", "Merchant", "Amount"]
    right_aligned = [False, True, False, True]
    if any(map(lambda note: note != "", notes)):
        columns.append(notes)
        column_names.append("Note")
        right_aligned.append(False)

    return format_as_table(columns, column_names, right_aligned)


@register_executable("find")
def find_transactions(args: List[str], data: Data) -> str:
    """Search for transactions meeting certain criteria."""
    return ""


@register_executable("del")
def delete_transaction(args: List[str], data: Data) -> str:
    """Delete a transaction from the record."""
    return ""


@register_executable("edit")
def edit_transaction(args: List[str], data: Data) -> str:
    """Make changes to a previously recorded transaction."""
    return ""


@register_executable("stat")
def generate_statement(args: List[str], data: Data) -> str:
    """Generate a statement for a range of transactions."""
    return ""


@register_executable("cat")
def categorize_transaction(args: List[str], data: Data) -> str:
    """Fit transations into categories."""
    return ""


# MERCHANTS

@register_executable("mer")
def display_merchants(args: List[str], data: Data) -> str:
    """Print all recorded merchants and their nicknames."""
    if len(args) > 0:
        processed_args = preprocess_args(args, [str])
    else:
        processed_args = [None]

    merchant_name, = processed_args

    if merchant_name is None:
        merchant_ids = list(data.merchants._all_ids())
    else:
        merchant_ids = [
            data.merchants.get_merchant_id(merchant_name)
        ]

    output_lines = list()

    for merchant_id in merchant_ids:
        full_name = data.merchants.get_merchant_full_name(merchant_id)
        output_lines.append(
            f"{full_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})"
        )
        for nickname in data.merchants.get_merchant_nicknames(merchant_id):
            output_lines.append(f"  {nickname}")

    return '\n'.join(output_lines)


@register_executable("est")
def establish_merchant(args: List[str], data: Data) -> str:
    """Establish a new merchant for the records."""
    processed_args = preprocess_args(args, [str])
    merchant_name, = processed_args
    data.merchants.add_merchant(merchant_name)
    merchant_id = data.merchants.get_merchant_id(merchant_name)
    return '\n'.join([
        "establishing merchant:",
        f"  {merchant_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})"
    ])


@register_executable("demo")
def demolish_merchant(args: List[str], data: Data) -> str:
    """Delete (or "demolish") a recorded merchant."""
    processed_args = preprocess_args(args, [str])
    merchant_name, = processed_args
    merchant_id = data.merchants.get_merchant_id(merchant_name)
    merchant_name = data.merchants.get_merchant_full_name(merchant_id)
    transactions = data.ledger.find_transactions_by_merchant_id(merchant_id)
    if len(transactions) > 0:
        return "cannot demolish a merchant that has transactions"
    data.merchants.delete_merchant(merchant_name)
    return '\n'.join([
        "demolishing merchant:",
        f"  {merchant_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})"
    ])


@register_executable("remo")
def remodel_merchant(args: List[str], data: Data) -> str:
    """Edit (or "remodel") an existing merchant."""
    processed_args = preprocess_args(args, [str, str])
    merchant_name, new_name = processed_args
    merchant_id = data.merchants.get_merchant_id(merchant_name)
    old_name = data.merchants.get_merchant_full_name(merchant_id)
    data.merchants.rename_merchant(merchant_id, new_name)
    return '\n'.join([
        "remodeling merchant:",
        f"  {old_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})",
        f"  {new_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})"
    ])


@register_executable("nick")
def nickname_merchant(args: List[str], data: Data) -> str:
    """Add a nickname to an existing merchant."""
    processed_args = preprocess_args(args, [str, str])
    merchant_name, nickname = processed_args
    merchant_id = data.merchants.get_merchant_id(merchant_name)
    full_name = data.merchants.get_merchant_full_name(merchant_id)
    data.merchants.add_nickname(merchant_name, nickname)
    return '\n'.join([
        "nicknaming merchant:",
        f"  {full_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})",
        f"  {nickname}"
    ])


@register_executable("denk")
def de_nickname_merchant(args: List[str], data: Data) -> str:
    """Delete a nickname from an merchant."""
    processed_args = preprocess_args(args, [str])
    nickname, = processed_args
    merchant_id = data.merchants.get_merchant_id(nickname)
    full_name = data.merchants.get_merchant_full_name(merchant_id)
    data.merchants.delete_nickname(nickname)
    return '\n'.join([
        "deleting merchant nickname:",
        f"  {full_name} ({id_to_hex(merchant_id, MERCHANT_ID_SIZE)})",
        f"  {nickname}"
    ])


# MISCELLANEOUS

@register_executable("")
def reprompt_user(args: List[str], data: Data) -> str:
    """Do nothing.

    This executable exists so that typing nothing at the command line and
    hitting the Enter key will just cause the prompt to reappear.
    """
    args = preprocess_args(args, [])
    return ""
