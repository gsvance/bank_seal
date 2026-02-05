#from config import Config
#from ledger import Date, Money, Ledger, Transaction, LedgerRow
#from merchants import Merchants, Merchant


class Status:

    def __init__(self, exit_flag: bool) -> None:
        self.exit_flag = exit_flag
        # TODO: Add some other stuff, like an unsaved data flag


class Data:

    def __init__(self, config_name: str, new_config: bool) -> None:
        self.status = Status(False)

    @property
    def exiting(self) -> bool:
        return self.status.exit_flag
