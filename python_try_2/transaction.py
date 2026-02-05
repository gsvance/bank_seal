"""A class representing a single monetary transation in the ledger.

Last modified 14 Oct 2023 by Greg Vance.
"""


from typing import Any, Dict, Tuple

from date import Date
from merchants import MERCHANT_ID_SIZE
from money import Money
from unique_id import UniqueID, HexID, id_to_hex, hex_to_id


class Transaction:
    """An object representing a single, mutable monetary transaction.

    The representation includes a date of transaction, a merchant identifier,
    an amount of money, and an optional note for other details. Each of these
    attributes should be considered public and mutable. Transactions can be
    ordered relative to one another and have some other convenience features.
    """

    __slots__ = (
        ("date", "merchant_id", "amount", "note")  # Saved attributes
        + ("subtotal", "transaction_id")  # Temporary (unsaved) attributes
    )

    # Constructors

    def __init__(
        self,
        date: Date,
        merchant_id: UniqueID,
        amount: Money,
        note: str = ""
    ) -> None:
        """Construct a new Transaction object with the provided components.

        The note is an optional string describing any details of the monetary
        transaction that are not captured by the date, merchant, or amount.
        """
        self.date = date
        self.merchant_id = merchant_id
        self.amount = amount
        self.note = note

        # These temporary attribute are used by the Ledger class but are not
        # serialized when a Transaction object is saved to a file
        self.subtotal: Money | None = None
        self.transaction_id: UniqueID | None = None

    @classmethod
    def deserialize(cls, obj: Dict[str, Any]) -> 'Transaction':
        """Reconstruct a transaction which was serialized to a JSON object."""
        assert set(obj.keys()) == {
            "class", "date", "merchant_id", "amount", "note"
        }
        assert obj["class"] == "Transaction"
        assert isinstance(obj["date"], dict)
        assert isinstance(obj["merchant_id"], HexID)
        assert isinstance(obj["amount"], dict)
        assert isinstance(obj["note"], str)

        date = Date.deserialize(obj["date"])
        merchant_id = hex_to_id(obj["merchant_id"])
        amount = Money.deserialize(obj["amount"])
        return Transaction(date, merchant_id, amount, obj["note"])

    # Output methods

    def __repr__(self) -> str:
        """Generate a Python-accurate repr of the Transaction object."""
        date = repr(self.date)
        hex_id = "0x" + id_to_hex(self.merchant_id, MERCHANT_ID_SIZE)
        amount = repr(self.amount)
        note = repr(self.note) if self.note != "" else None

        if note is None:
            return f"Transaction({date}, {hex_id}, {amount})"
        else:
            return f"Transaction({date}, {hex_id}, {amount}, {note})"

    def serialize(self) -> Dict[str, Any]:
        """Convert this transaction to an object dict for JSON processing."""
        return {
            "class": "Transaction",
            "date": self.date.serialize(),
            "merchant_id": id_to_hex(self.merchant_id, MERCHANT_ID_SIZE),
            "amount": self.amount.serialize(),
            "note": self.note,
        }

    # Methods for sign-restricted access to the amount

    @property
    def positive_amount(self) -> Money:
        """The amount for this transaction, but only if positive."""
        return max(self.amount, Money(0))

    @property
    def negative_amount(self) -> Money:
        """The ammount for this transaction, but only if negative."""
        return min(self.amount, Money(0))

    # Attribute-mutating methods

    def erase_note(self) -> None:
        """Erase the contents of the Transaction's note string (if any)."""
        self.note = ""

    def reset_temporary_attributes(self) -> None:
        """Reset all temporary attributes used by the Ledger class to None."""
        self.subtotal = None
        self.transaction_id = None

    # Ordering of transactions (primarily chronological)

    def _order_key(self) -> Tuple[Date, Money, int, str]:
        # Assemble a standard tuple that can be used for ordering relations
        # The minus sign on self.amount arranges those in descending order
        return (self.date, -self.amount, self.merchant_id, self.note)

    def __lt__(self, other: 'Transaction') -> bool:
        return self._order_key() < other._order_key()

    def __le__(self, other: 'Transaction') -> bool:
        return self._order_key() <= other._order_key()

    def __eq__(self, other: 'Transaction') -> bool:
        return self._order_key() == other._order_key()

    def __ne__(self, other: 'Transaction') -> bool:
        return self._order_key() != other._order_key()

    def __gt__(self, other: 'Transaction') -> bool:
        return self._order_key() > other._order_key()

    def __ge__(self, other: 'Transaction') -> bool:
        return self._order_key() >= other._order_key()
