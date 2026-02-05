# test_transaction.py

"""Unit tests for the Transaction class.

Last modified 19 Feb 2023 by Greg Vance.
"""


import unittest

from transaction import Transaction
from date import Date
from merchants import Merchants
from money import Money


class TestTransactionClass(unittest.TestCase):

    def test_Transaction_init(self):
        d = Date.parse("11 Feb 2023")
        m = Merchants()
        m.add_merchant("Fry's Food and Drug")
        i = m.get_merchant_id("Fry's Food and Drug")
        a = Money.parse("$95.93")

        t = Transaction(d, i, a)
        self.assertEqual(t.date, Date(2023, 2, 11))
        self.assertEqual(t.merchant_id,
                         m.get_merchant_id("Fry's Food and Drug"))
        self.assertEqual(t.amount, Money(9593))
        self.assertEqual(t.note, "")

        t = Transaction(d, i, a, "picked up assorted groceries")
        self.assertEqual(t.date, Date(2023, 2, 11))
        self.assertEqual(t.merchant_id,
                         m.get_merchant_id("Fry's Food and Drug"))
        self.assertEqual(t.amount, Money(9593))
        self.assertEqual(t.note, "picked up assorted groceries")

    def test_Transaction_repr(self):
        d = Date.parse("8 Sep 1998")
        m = Merchants()
        m.add_merchant("Market Basket")
        i = m.get_merchant_id("Market Basket")
        h = hex(i)
        a = Money.parse("$12.99")

        t = Transaction(d, i, a)
        self.assertEqual(
            repr(t),
            f"Transaction(Date(1998, 9, 8), {h}, Money(1299))"
        )

        t = Transaction(d, i, a, "NH groceries")
        self.assertEqual(
            repr(t),
            f"Transaction(Date(1998, 9, 8), {h}, Money(1299), 'NH groceries')"
        )
