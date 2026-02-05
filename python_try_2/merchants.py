"""A merchant database class for storing merchants by full name and nickname.

Last modified 14 Oct 2023 by Greg Vance.
"""

from collections.abc import KeysView
import json
from typing import Dict, Set

from cryptography import encypher, decypher
from unique_id import (
    UniqueID, HexID, generate_new_unique_id, id_to_hex, hex_to_id
)

# Merchant IDs use a certain number of hex digits
MERCHANT_ID_SIZE = 8  # hex digits == 32 bits

# This limits the maximum number of available IDs
_MAX_MERCHANT_IDS = 16 ** MERCHANT_ID_SIZE


class Merchants:
    """Merchant database for storing full names, nicknames, and merchant IDs.

    This class represents each merchant internally as a unique "full name"
    string associated with a unique merchant ID in hex that is randomly
    generated. Each merchant can also optionally have "nicknames," which are
    other strings that also map uniquely to the same merchant ID.
    """

    __slots__ = ("_full_names_by_id", "_nicknames_by_id", "_ids_by_name")

    # Constructors

    def __init__(self) -> None:
        """Construct a new Merchants database by setting up its internals."""
        self._full_names_by_id: Dict[UniqueID, str] = dict()
        self._nicknames_by_id: Dict[UniqueID, Set[str]] = dict()
        self._ids_by_name: Dict[str, UniqueID] = dict()

    @classmethod
    def from_file(cls, file_name: str) -> 'Merchants':
        """Create a new Merchants object by deserializing file contents."""
        with open(file_name, "rb") as merchants_file:
            content = merchants_file.read()
        obj = json.loads(decypher(content))

        assert set(obj.keys()) == {
            "class", "full_names_by_id", "nicknames_by_id"
        }
        assert obj["class"] == "Merchants"
        assert isinstance(obj["full_names_by_id"], dict)
        assert isinstance(obj["nicknames_by_id"], dict)

        merchants = Merchants()
        for hex_id, full_name in obj["full_names_by_id"].items():
            assert isinstance(hex_id, str)
            assert isinstance(full_name, str)
            merchant_id = hex_to_id(HexID(hex_id))
            merchants.add_merchant(full_name, with_merchant_id=merchant_id)
        for hex_id, nicknames in obj["nicknames_by_id"].items():
            assert isinstance(hex_id, str)
            assert isinstance(nicknames, list)
            merchant_id = hex_to_id(HexID(hex_id))
            for nickname in nicknames:
                assert isinstance(nickname, str)
                merchants.add_nickname(merchant_id, nickname)
        return merchants

    # Output methods

    def __repr__(self) -> str:
        """Simple, uninformative repr string for Merchants object."""
        n_names, n_ids = self.n_names, self.n_ids
        names_str = f"{n_names} names" if n_names != 1 else "1 name"
        ids_str = f"{n_ids} IDs" if n_ids != 1 else "1 ID"
        return f"<Merchants object with {names_str} and {ids_str}>"

    def to_file(self, fname: str) -> None:
        """Serialize the Merchants object and write its data out to file."""
        obj = {
            "class": "Merchants",
            "full_names_by_id": {
                id_to_hex(merchant_id, MERCHANT_ID_SIZE): full_name
                for merchant_id, full_name
                in self._full_names_by_id.items()
            },
            "nicknames_by_id": {
                id_to_hex(merchant_id, MERCHANT_ID_SIZE): list(nicknames)
                for merchant_id, nicknames
                in self._nicknames_by_id.items()
            },
        }

        content = encypher(json.dumps(obj, indent=' ' * 2))
        with open(fname, "wb") as merchants_file:
            merchants_file.write(content)

    # Internal methods for clarified keyset access

    def _all_names(self) -> KeysView[str]:
        # Get a view to the keyset of all full names *and* nicknames
        return self._ids_by_name.keys()

    def _all_ids(self) -> KeysView[UniqueID]:
        # Get a view to the keyset of all merchant IDs
        return self._full_names_by_id.keys()

    # Integer-valued properties

    @property
    def n_names(self) -> int:
        """Total number of full names *and* nicknames stored."""
        return len(self._all_names())

    @property
    def n_ids(self) -> int:
        """Number of merchant IDs stored."""
        return len(self._all_ids())

    @property
    def n_full_names(self) -> int:
        """Number of full names stored (equal to n_ids)."""
        return self.n_ids

    @property
    def n_nicknames(self) -> int:
        """Number of nicknames stored (equal to n_names - n_full_names)."""
        return self.n_names - self.n_full_names

    # Lookup methods

    def get_merchant_id(self, name: str) -> UniqueID:
        """Find the merchant ID associated with a full name or nickname."""
        try:
            return self._ids_by_name[name]
        except KeyError:
            raise KeyError(f"merchant name {name!r} was not found")

    def _resolve_to_merchant_id(self, name_or_id: str | UniqueID) -> UniqueID:
        # Resolve any name or merchant ID consistently to a merchant ID
        if isinstance(name_or_id, int):
            merchant_id: UniqueID = name_or_id
            if merchant_id not in self._all_ids():
                raise KeyError(f"merchant id {merchant_id!r} was not found")
        else:
            name: str = name_or_id
            merchant_id = self.get_merchant_id(name)
        return merchant_id

    def get_merchant_full_name(self, name_or_id: str | UniqueID) -> str:
        """Return the full name of a merchant."""
        merchant_id = self._resolve_to_merchant_id(name_or_id)
        return self._full_names_by_id[merchant_id]

    def get_merchant_nicknames(self, name_or_id: str | UniqueID) -> Set[str]:
        """Return a copy of the set of all nicknames for a merchant."""
        merchant_id = self._resolve_to_merchant_id(name_or_id)
        return set(self._nicknames_by_id[merchant_id])

    # Insertion methods

    def _create_new_merchant_id(self) -> UniqueID:
        # Generate a new merchant ID if there is still room for one
        if self.n_ids < _MAX_MERCHANT_IDS:
            return generate_new_unique_id(MERCHANT_ID_SIZE, self._all_ids())
        else:
            raise RuntimeError("maximum number of merchant IDs reached")

    def add_merchant(
        self,
        full_name: str,
        *,
        with_merchant_id: UniqueID | None = None
    ) -> None:
        """Add a new merchant using the provided full name.

        A randomized merchant ID will be generated for the new merchant unless
        a chosen merchant ID is passed in using the with_merchant_id parameter.
        """
        if full_name in self._all_names():
            raise ValueError(
                f"proposed name {full_name!r} already refers to a merchant"
            )

        if with_merchant_id is None:
            merchant_id = self._create_new_merchant_id()
        else:
            merchant_id = with_merchant_id
            if merchant_id in self._all_ids():
                raise ValueError("specified merchant ID is already in use")
        self._full_names_by_id[merchant_id] = full_name
        self._nicknames_by_id[merchant_id] = set()
        self._ids_by_name[full_name] = merchant_id

    def add_nickname(self, name_or_id: str | UniqueID, nickname: str) -> None:
        """Add a new nickname to an existing merchant."""
        merchant_id = self._resolve_to_merchant_id(name_or_id)

        if nickname in self._all_names():
            raise ValueError(
                f"proposed name {nickname!r} already refers to a merchant"
            )

        self._nicknames_by_id[merchant_id].add(nickname)
        self._ids_by_name[nickname] = merchant_id

    # Removal methods

    def delete_nickname(self, nickname: str) -> None:
        """Delete a nickname without otherwise affecting the merchant."""
        merchant_id = self.get_merchant_id(nickname)
        full_name = self.get_merchant_full_name(merchant_id)

        if nickname == full_name:
            raise ValueError(f"the name {nickname!r} is not a nickname")

        del self._ids_by_name[nickname]
        self._nicknames_by_id[merchant_id].remove(nickname)

    def delete_merchant(self, name_or_id: str | UniqueID) -> None:
        """Delete a merchant and all of its associated nicknames."""
        merchant_id = self._resolve_to_merchant_id(name_or_id)
        full_name = self.get_merchant_full_name(merchant_id)
        nicknames = self.get_merchant_nicknames(merchant_id)

        for nickname in nicknames:
            self.delete_nickname(nickname)
        del self._ids_by_name[full_name]
        del self._full_names_by_id[merchant_id]

    # Editing methods

    def rename_merchant(
        self,
        name_or_id: str | UniqueID,
        new_full_name: str
    ) -> None:
        """Replace the full name associated with a merchant ID."""
        merchant_id = self._resolve_to_merchant_id(name_or_id)
        old_full_name = self.get_merchant_full_name(merchant_id)

        del self._ids_by_name[old_full_name]
        self._ids_by_name[new_full_name] = merchant_id
        self._full_names_by_id[merchant_id] = new_full_name
