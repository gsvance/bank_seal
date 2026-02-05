"""A Ledger is a database object containing many monetary transactions.

Last modified 14 Oct 2023 by Greg Vance.
"""


from collections.abc import KeysView
import json
from typing import Dict, List

from cryptography import encypher, decypher
from date import Date
from money import Money
from transaction import Transaction
from unique_id import (
    UniqueID, HexID, generate_new_unique_id, id_to_hex, hex_to_id
)


# Transaction IDs use a certain number of hex digits
TRANSACTION_ID_SIZE = 8  # hex digits == 32 bits

# This limits the maximum number of available IDs
_MAX_TRANSACTION_IDS = 16 ** TRANSACTION_ID_SIZE


class Ledger:
    """The Ledger object is an organized container for transactions.

    The Ledger interface handles adding and deleting transactions, editing
    transactions, and various types of transaction queries. It assigns
    transaction IDs internally, sorts the transactions, and manages subtotal
    calculations.
    """

    __slots__ = ("_transactions_by_id", "_sorted_ids")

    # Constructors

    def __init__(self) -> None:
        """Construct a new Ledger by initializing its internals."""
        self._transactions_by_id: Dict[UniqueID, Transaction] = dict()
        self._sorted_ids: List[UniqueID] = list()

    @classmethod
    def from_file(cls, file_name: str) -> 'Ledger':
        """Create a new Transaction object by deserializing file contents."""
        with open(file_name, "rb") as ledger_file:
            contents = ledger_file.read()
        obj = json.loads(decypher(contents))

        assert set(obj.keys()) == {"class", "transactions_by_id"}
        assert obj["class"] == "Ledger"
        assert isinstance(obj["transactions_by_id"], dict)

        ledger = Ledger()
        for hex_id, transaction_obj in obj["transactions_by_id"].items():
            assert isinstance(hex_id, str)
            assert isinstance(transaction_obj, dict)
            transaction_id = hex_to_id(HexID(hex_id))
            transaction = Transaction.deserialize(transaction_obj)
            ledger.insert_transaction(
                transaction,
                with_transaction_id=transaction_id,
                skip_organize=True
            )
        ledger._organize()
        return ledger

    # Output methods

    def __repr__(self) -> str:
        """Simple, uninformative repr string for Ledger object."""
        n_transactions = len(self)
        transactions_str = f"{n_transactions} transaction"
        if n_transactions != 1:
            transactions_str += 's'
        return f"<Ledger object with {transactions_str}>"

    def to_file(self, fname: str) -> None:
        """Serialize the Ledger object and write its data out to file."""
        obj = {
            "class": "Ledger",
            "transactions_by_id": {
                id_to_hex(transaction_id, TRANSACTION_ID_SIZE):
                    self._transactions_by_id[transaction_id].serialize()
                for transaction_id in self._sorted_ids
            },
        }

        content = encypher(json.dumps(obj, indent=' ' * 2))
        with open(fname, "wb") as ledger_file:
            ledger_file.write(content)

    # Internal method for clarified keyset access

    def _all_ids(self) -> KeysView[UniqueID]:
        # Get a view to the keyset of all transaction IDs
        return self._transactions_by_id.keys()

    # Methods and properties relating to size

    @property
    def n_ids(self) -> int:
        """Number of transaction IDs stored."""
        return len(self._all_ids())

    def __len__(self) -> int:
        """Return the number of transactions in the Ledger (equal to n_ids)."""
        return self.n_ids

    # Internal organizational methods

    def _organize(self) -> None:
        # Internally straighten out the Ledger to keep it tidy and efficient
        self._sort_transactions()
        self._compute_subtotals()

    def _sort_transactions(self) -> None:
        # Sort the transaction IDs list to show the correct Transaction order
        self._sorted_ids.sort(
            key=lambda unique_id: self._transactions_by_id[unique_id]
        )

    def _compute_subtotals(self) -> None:
        # Loop through the Transaction objects and tag each with a subtotal
        subtotal = Money(0)
        for transaction_id in self._sorted_ids:
            transaction = self._transactions_by_id[transaction_id]
            subtotal = subtotal + transaction.amount
            transaction.subtotal = subtotal

    # Methods for searching

    def _validate_transaction_id(self, transaction_id: UniqueID) -> None:
        # Raise an error if the given transaction ID is not present
        if transaction_id not in self._all_ids():
            raise ValueError(
                f"transaction ID {transaction_id!r} was not found"
            )

    def find_transaction_by_id(self, transaction_id: UniqueID) -> Transaction:
        """Return a single transaction based on its transaction ID."""
        self._validate_transaction_id(transaction_id)
        return self._transactions_by_id[transaction_id]

    def find_newest_transactions(
        self,
        n_newest: int
    ) -> List[Transaction]:
        """Find the newest transactions in the Ledger."""
        if n_newest < 0:
            return self.find_oldest_transactions(-n_newest)
        if n_newest > len(self):
            n_newest = len(self)

        newest_transactions = map(
            lambda transaction_id: self._transactions_by_id[transaction_id],
            self._sorted_ids[-n_newest:]
        )
        return list(newest_transactions)

    def find_oldest_transactions(
        self,
        n_oldest: int
    ) -> List[Transaction]:
        """Find the oldest transactions in the Ledger."""
        if n_oldest < 0:
            return self.find_newest_transactions(-n_oldest)
        if n_oldest > len(self):
            n_oldest = len(self)

        oldest_transactions = map(
            lambda transaction_id: self._transactions_by_id[transaction_id],
            self._sorted_ids[:n_oldest]
        )
        return list(oldest_transactions)

    def find_transactions_by_date(
        self,
        date: Date
    ) -> List[Transaction]:
        """Find transactions in the Ledger matching a single date."""
        return self.find_transactions_in_date_range(date, date)

    def find_transactions_in_date_range(
        self,
        start_date: Date,
        end_date: Date
    ) -> List[Transaction]:
        """Find transactions in the Ledger within a given date range."""
        if end_date < start_date:
            raise ValueError("date range end cannot come before start")

        sorted_transactions = map(
            lambda transaction_id: self._transactions_by_id[transaction_id],
            self._sorted_ids
        )
        matching_transactions = filter(
            lambda transaction: start_date <= transaction.date <= end_date,
            sorted_transactions
        )
        return list(matching_transactions)

    def find_transactions_by_merchant_id(
        self,
        merchant_id: UniqueID
    ) -> List[Transaction]:
        """Find transactions in the Ledger that match a given merchant ID."""
        sorted_transactions = map(
            lambda transaction_id: self._transactions_by_id[transaction_id],
            self._sorted_ids
        )
        matching_transactions = filter(
            lambda transaction: transaction.merchant_id == merchant_id,
            sorted_transactions
        )
        return list(matching_transactions)

    def find_transactions_by_amount(
        self,
        amount: Money
    ) -> List[Transaction]:
        """Find Ledger transactions matching a specific monetary amount."""
        return self.find_transactions_in_amount_range(amount, amount)

    def find_transactions_in_amount_range(
        self,
        lower_amount: Money,
        upper_amount: Money
    ) -> List[Transaction]:
        """Find transactions in the Ledger within a monetary amount range."""
        if upper_amount < lower_amount:
            raise ValueError(
                "upper amount for range is smaller than lower amount"
            )

        sorted_transactions = map(
            lambda transaction_id: self._transactions_by_id[transaction_id],
            self._sorted_ids
        )
        matching_transactions = filter(
            lambda transaction:
                lower_amount <= transaction.amount <= upper_amount,
            sorted_transactions
        )
        return list(matching_transactions)

    # Methods for inserting and deleting

    def _create_new_transaction_id(self) -> UniqueID:
        # Generate a new transaction ID if there is still room for one
        if self.n_ids < _MAX_TRANSACTION_IDS:
            return generate_new_unique_id(TRANSACTION_ID_SIZE, self._all_ids())
        else:
            raise RuntimeError("maximum number of transaction IDs reached")

    def insert_transaction(
        self,
        transaction: Transaction,
        *,
        with_transaction_id: UniqueID | None = None,
        skip_organize: bool = False
    ) -> None:
        """Add a new transaction to the Ledger and assign it an ID.

        A randomized transaction ID will be assigned to the new transaction
        unless a pre-chosen transaction ID is passed in using the
        with_transaction_id parameter. The skip_organize flag can be used to
        save on execution time when inserting large numbers of transactions at
        once.
        """
        if with_transaction_id is None:
            transaction_id = self._create_new_transaction_id()
        else:
            transaction_id = with_transaction_id
            if transaction_id in self._all_ids():
                raise ValueError("specified transaction ID is already in use")

        self._transactions_by_id[transaction_id] = transaction
        self._sorted_ids.append(transaction_id)
        transaction.transaction_id = transaction_id

        if not skip_organize:
            self._organize()

    def delete_transaction(
        self,
        transaction_id: UniqueID,
        *,
        skip_organize: bool = False
    ) -> None:
        """Remove a transaction from the Ledger by giving its ID.

        The skip_organize flag can be used to save on execution time when
        deleting large numbers of transactions at once.
        """
        self._validate_transaction_id(transaction_id)

        self._sorted_ids.remove(transaction_id)
        del self._transactions_by_id[transaction_id]

        if not skip_organize:
            self._organize()

    # Methods for updating transactions

    def update_transaction_date(
        self,
        transaction_id: UniqueID,
        new_date: Date
    ) -> None:
        """Replace the date on an existing transaction by ID."""
        transaction = self.find_transaction_by_id(transaction_id)
        transaction.date = new_date
        self._organize()

    def update_transaction_merchant_id(
        self,
        transaction_id: UniqueID,
        new_merchant_id: UniqueID
    ) -> None:
        """Replace the merchant ID on an existing transaction by ID."""
        transaction = self.find_transaction_by_id(transaction_id)
        transaction.merchant_id = new_merchant_id
        self._organize()

    def update_transaction_amount(
        self,
        transaction_id: UniqueID,
        new_amount: Money
    ) -> None:
        """Replace the monetary amount on an existing transaction by ID."""
        transaction = self.find_transaction_by_id(transaction_id)
        transaction.amount = new_amount
        self._organize()

    def update_transaction_note(
        self,
        transaction_id: UniqueID,
        new_note: str | None
    ) -> None:
        """Replace the note string on an existing transaction by ID.

        If the new_note value is None, then the transaction's note string will
        be erased entirely.
        """
        transaction = self.find_transaction_by_id(transaction_id)
        if new_note is not None:
            transaction.note = new_note
        else:
            transaction.erase_note()
        self._organize()
