"""All sorts of fiddly stuff for handling the configuration info.

Note that there is a difference between the Config class (which should be the
only thing getting used outside this file) and the ConfigDict type, which is a
dictionary that lives inside the Config class and has the actual content that
gets written to the JSON files on disk.

Last modified 25 Sep 2023 by Greg Vance.
"""

import json
import os.path
from typing import Any, Dict, Union

from paths import make_config_path, make_ledger_path, make_merchants_path


_ConfigKey = str
_ConfigValue = Union[str, bool]
_ConfigDict = Dict[_ConfigKey, _ConfigValue]

# The name on the file containing the default configuration
_DEFAULT_CONFIG_NAME = "DEFAULT"


class Config:

    def __init__(self, config_dict: _ConfigDict):
        self._config_dict = config_dict

    @classmethod
    def load(cls, config_name: str, new_config: bool) -> 'Config':
        if new_config:
            _create_new_configuration(config_name)
        return Config(_load_configuration(config_name))

    @property
    def config_name(self) -> str:
        name = self._config_dict["config name"]
        assert isinstance(name, str)
        return name

    def get_config_path(self, ) -> str:
        return make_config_path(self.config_name)

    @property
    def ledger_name(self) -> str:
        name = self._config_dict["ledger name"]
        assert isinstance(name, str)
        return name

    def get_ledger_path(self) -> str:
        return make_ledger_path(self.ledger_name)

    @property
    def merchants_name(self) -> str:
        name = self._config_dict["merchants name"]
        assert isinstance(name, str)
        return name

    def get_merchants_path(self) -> str:
        return make_merchants_path(self.merchants_name)

    def save(self):
        _save_configuration(self._config_dict)

    def read(self, key: str) -> Any | None:
        return self._config_dict.get(key)

    def write(self, key: str, value: Any) -> None:
        self._config_dict[key] = value


def _load_default_configuration() -> _ConfigDict:
    """Load the default configuration from disk."""

    default_config_path = make_config_path(_DEFAULT_CONFIG_NAME)
    if not os.path.exists(default_config_path):
        raise IOError("default configuration file was not found!")
    with open(default_config_path, "r") as default_config_file:
        default_config = json.load(default_config_file)

    assert default_config["config name"] == _DEFAULT_CONFIG_NAME
    return default_config


def _load_configuration(config_name: str) -> _ConfigDict:
    """Load a named configuration from its file."""

    config_path = make_config_path(config_name)
    if not os.path.exists(config_path):
        raise ValueError(
            f"no configuration named {config_name} currently exists"
        )
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    default_config = _load_default_configuration()
    assert set(config.keys()) == set(default_config.keys())
    assert config["config name"] == config_name

    return config


def _save_configuration(config: _ConfigDict) -> None:
    """Save the given configuration to a file with an appropriate name."""

    default_config = _load_default_configuration()
    assert set(config.keys()) == set(default_config.keys())
    assert isinstance(config["config name"], str)

    config_path = make_config_path(config["config name"])
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=' ' * 2)


def _create_new_configuration(new_config_name: str) -> None:
    """Copy the default configuration to a new file with the provided name."""
    default_config = _load_default_configuration()
    new_config = default_config.copy()
    new_config["config name"] = new_config_name
    config_path = make_config_path(new_config["config name"])
    if os.path.exists(config_path):
        raise IOError("config file already exisits!")
    _save_configuration(new_config)
