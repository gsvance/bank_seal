"""Construction of paths to application data files in a standardized way.

This code exists in a separate file mostly to prevent circular imports or code
repetition amongst the various classes that need to access the file system.

Last modified 25 Sep 2023 by Greg Vance.
"""

import os.path


SOURCE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_DIRECTORY = os.path.join(SOURCE_DIRECTORY, "data")

CONFIG_SUFFIX = "_config.json"
LEDGER_SUFFIX = "_ledger.json"
MERCHANTS_SUFFIX = "_merchants.json"


def make_config_path(config_name: str) -> str:
    """Construct the absolute path to the file holding a configuration."""
    return os.path.join(DATA_DIRECTORY, config_name + CONFIG_SUFFIX)


def make_ledger_path(ledger_name: str) -> str:
    """Construct the absolute path to the file holding a Ledger object."""
    return os.path.join(DATA_DIRECTORY, ledger_name + LEDGER_SUFFIX)


def make_merchants_path(merchants_name: str) -> str:
    """Construct the absolute path to the file holding a Merchants object."""
    return os.path.join(DATA_DIRECTORY, merchants_name + MERCHANTS_SUFFIX)
