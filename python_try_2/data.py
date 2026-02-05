"""A simple aggregate class that collects all program data into one object.

At present, the Data class contains attributes for Config, Ledger, and
Merchants objects that can be saved to and loaded from files on disk. The
attributes should all be treated as public in code using this class.

Last modified 25 Sep 2023 by Greg Vance.
"""

from config import Config
from ledger import Ledger
from merchants import Merchants


class Data:

    def __init__(
        self,
        config: Config,
        ledger: Ledger,
        merchants: Merchants,
    ) -> None:
        self.config = config
        self.ledger = ledger
        self.merchants = merchants

    @classmethod
    def load(cls, config_name: str, new_config: bool) -> 'Data':
        config = Config.load(config_name, new_config)
        ledger = Ledger.from_file(config.get_ledger_path())
        merchants = Merchants.from_file(config.get_merchants_path())
        return Data(config, ledger, merchants)

    def save(self, *, save_config_too: bool = True) -> None:
        if save_config_too:
            self.config.save()
        self.ledger.to_file(self.config.get_ledger_path())
        self.merchants.to_file(self.config.get_merchants_path())
