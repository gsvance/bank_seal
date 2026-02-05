# test_date.py

"""Unit tests for the Date class.

Last modified 11 Feb 2023 by Greg Vance.
"""


import unittest
import datetime

from date import Date


class TestDateClass(unittest.TestCase):

    def test_Date_init(self):
        d = Date(2023, 2, 6)
        self.assertEqual(d._year, 2023)
        self.assertEqual(d._month, 2)
        self.assertEqual(d._day, 6)
        d = Date(1993, 4, 11)
        self.assertEqual(d._year, 1993)
        self.assertEqual(d._month, 4)
        self.assertEqual(d._day, 11)
        d = Date(2016, 2, 29)
        self.assertEqual(d._year, 2016)
        self.assertEqual(d._month, 2)
        self.assertEqual(d._day, 29)
        d = Date(1995, 10, 16)
        self.assertEqual(d._year, 1995)
        self.assertEqual(d._month, 10)
        self.assertEqual(d._day, 16)

    def test_Date_today(self):
        d = Date.today()
        today = datetime.date.today()
        self.assertEqual(d._year, today.year)
        self.assertEqual(d._month, today.month)
        self.assertEqual(d._day, today.day)

    def test_Date_infer_year(self):
        current_year = datetime.date.today().year
        for year in range(current_year - 30, current_year + 31):
            two_digit = year % 100
            d4 = Date.infer_year(year, 5, 20)
            self.assertEqual(d4._year, year)
            self.assertEqual(d4._month, 5)
            self.assertEqual(d4._day, 20)
            d2 = Date.infer_year(two_digit, 5, 20)
            self.assertEqual(d2._year, year)
            self.assertEqual(d2._month, 5)
            self.assertEqual(d2._day, 20)

        current_month = datetime.date.today().month
        for unbounded_month in range(current_month - 5, current_month + 6):
            if unbounded_month < 1:
                month = unbounded_month + 12
                year = current_year - 1
            elif unbounded_month > 12:
                month = unbounded_month - 12
                year = current_year + 1
            else:
                month = unbounded_month
                year = current_year
            d = Date.infer_year(None, month, 10)
            self.assertEqual(d._year, year)
            self.assertEqual(d._month, month)
            self.assertEqual(d._day, 10)

        self.assertRaises(ValueError, Date.infer_year, 321, 4, 10)
        self.assertRaises(ValueError, Date.infer_year, 54321, 4, 10)
        self.assertRaises(ValueError, Date.infer_year, -79, 4, 10)

    def test_Date_parse_succeeds(self):
        current_year = datetime.date.today().year

        d = Date.parse("12/22/2023")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("12/22/23")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("1/22/2023")
        self.assertEqual(d._month, 1)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("1/22/23")
        self.assertEqual(d._month, 1)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("12/6/2023")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 6)
        self.assertEqual(d._year, 2023)

        d = Date.parse("12/6/23")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 6)
        self.assertEqual(d._year, 2023)

        d = Date.parse("6/30")
        self.assertEqual(d._month, 6)
        self.assertEqual(d._day, 30)
        self.assertEqual(d._year, current_year)

        d = Date.parse("7/1")
        self.assertEqual(d._month, 7)
        self.assertEqual(d._day, 1)
        self.assertEqual(d._year, current_year)

        d = Date.parse("22 Dec 2023")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("22 Dec 23")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("22 Jan 2023")
        self.assertEqual(d._month, 1)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("22 Jan 23")
        self.assertEqual(d._month, 1)
        self.assertEqual(d._day, 22)
        self.assertEqual(d._year, 2023)

        d = Date.parse("6 Dec 2023")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 6)
        self.assertEqual(d._year, 2023)

        d = Date.parse("6 Dec 23")
        self.assertEqual(d._month, 12)
        self.assertEqual(d._day, 6)
        self.assertEqual(d._year, 2023)

        d = Date.parse("30 Jun")
        self.assertEqual(d._month, 6)
        self.assertEqual(d._day, 30)
        self.assertEqual(d._year, current_year)

        d = Date.parse("1 Jul")
        self.assertEqual(d._month, 7)
        self.assertEqual(d._day, 1)
        self.assertEqual(d._year, current_year)

    def test_Date_parse_fails(self):
        garbage = [
            "", "/", "//", "May", "13", "2012", " ",
            "11//2020", "/5/1999", "10/2/",
            "123/4/2007", "9/321/2009", "7/21/54321", "6/30/543",
            " Feb 21", "21  2011", "3 Mar 123", "4 Mar 54321",
            "234 Apr 2000", "5 Grb 2004", "12 Bla 97",
        ]
        for snotty_tissue in garbage:
            self.assertRaises(ValueError, Date.parse, snotty_tissue)

    def test_Date_str(self):
        d = Date(2023, 2, 6)
        self.assertEqual(str(d), "6 Feb 2023")
        d = Date(2002, 12, 25)
        self.assertEqual(str(d), "25 Dec 2002")
        d = Date(2011, 9, 30)
        self.assertEqual(str(d), "30 Sep 2011")
        d = Date(2018, 3, 10)
        self.assertEqual(str(d), "10 Mar 2018")

    def test_Date_repr(self):
        d = Date(2023, 2, 6)
        self.assertEqual(repr(d), "Date(2023, 2, 6)")
        d = Date(2005, 8, 1)
        self.assertEqual(repr(d), "Date(2005, 8, 1)")
        d = Date(1999, 11, 11)
        self.assertEqual(repr(d), "Date(1999, 11, 11)")
        d = Date(2015, 5, 20)
        self.assertEqual(repr(d), "Date(2015, 5, 20)")

    def test_Date_validate(self):
        with self.assertRaisesRegex(ValueError, r"year \d+ is before"):
            Date(1840, 5, 10)
        with self.assertRaisesRegex(ValueError, r"year \d+ is after"):
            Date(2300, 1, 31)
        with self.assertRaisesRegex(ValueError, "illegal month of the year"):
            Date(2013, 0, 12)
        with self.assertRaisesRegex(ValueError, "illegal month of the year"):
            Date(2013, 14, 27)
        with self.assertRaisesRegex(ValueError, "illegal day of the month"):
            Date(2013, 7, -4)
        with self.assertRaisesRegex(ValueError,
                                    "is after the end of the month"):
            Date(2013, 4, 31)
        with self.assertRaisesRegex(ValueError,
                                    "is after the end of the month"):
            Date(2021, 2, 29)

    def test_Date_name_of_month(self):
        d = Date(2023, 2, 6)
        self.assertEqual(d.name_of_month(), "Feb")
        d = Date(2008, 4, 12)
        self.assertEqual(d.name_of_month(), "Apr")
        d = Date(2015, 10, 24)
        self.assertEqual(d.name_of_month(), "Oct")
        d = Date(2020, 7, 17)
        self.assertEqual(d.name_of_month(), "Jul")
        d = Date(1996, 8, 2)
        self.assertEqual(d.name_of_month(), "Aug")

    def test_Date_length_of_month(self):
        d = Date(2023, 2, 6)
        self.assertEqual(d.length_of_month(), 28)
        d = Date(2024, 2, 18)
        self.assertEqual(d.length_of_month(), 29)
        d = Date(2012, 1, 29)
        self.assertEqual(d.length_of_month(), 31)
        d = Date(1994, 4, 11)
        self.assertEqual(d.length_of_month(), 30)
        d = Date(1999, 8, 11)
        self.assertEqual(d.length_of_month(), 31)

    def test_Date_in_leap_year(self):
        d = Date(2023, 2, 6)
        self.assertFalse(d.in_leap_year())
        d = Date(2024, 3, 17)
        self.assertTrue(d.in_leap_year())
        d = Date(2004, 9, 3)
        self.assertTrue(d.in_leap_year())
        d = Date(2000, 5, 9)
        self.assertTrue(d.in_leap_year())
        d = Date(1999, 6, 11)
        self.assertFalse(d.in_leap_year())

    def test_Date_properties(self):
        d = Date(2023, 2, 6)
        self.assertEqual(d.year, 2023)
        self.assertEqual(d.month, 2)
        self.assertEqual(d.day, 6)
        d = Date(1995, 6, 22)
        self.assertEqual(d.year, 1995)
        self.assertEqual(d.month, 6)
        self.assertEqual(d.day, 22)

    def test_Date_order_key(self):
        d = Date(2023, 2, 6)
        self.assertEqual(d._order_key(), (2023, 2, 6))
        d = Date(1998, 11, 24)
        self.assertEqual(d._order_key(), (1998, 11, 24))
        d = Date(2001, 5, 18)
        self.assertEqual(d._order_key(), (2001, 5, 18))

    def test_Date_comparisons(self):
        d1 = Date(1993, 4, 11)
        d2 = Date(1995, 10, 16)
        d3 = Date(1995, 10, 16)
        d4 = Date(2015, 4, 25)
        d5 = Date(2015, 5, 20)
        d6 = Date(2023, 5, 30)

        self.assertLess(d1, d5)
        self.assertFalse(d1 >= d5)
        self.assertLess(d3, d4)
        self.assertFalse(d3 >= d4)

        self.assertLessEqual(d2, d3)
        self.assertFalse(d2 > d3)
        self.assertLessEqual(d2, d6)
        self.assertFalse(d2 > d6)

        self.assertEqual(d2, d3)
        self.assertFalse(d2 != d3)
        self.assertNotEqual(d3, d4)
        self.assertFalse(d3 == d4)

        self.assertGreater(d5, d4)
        self.assertFalse(d5 <= d4)
        self.assertGreater(d6, d1)
        self.assertFalse(d6 <= d1)

        self.assertGreaterEqual(d2, d3)
        self.assertFalse(d2 < d3)
        self.assertGreaterEqual(d5, d4)
        self.assertFalse(d5 < d4)

    def test_Date_hash(self):
        d1 = Date(2023, 2, 6)
        d2 = Date(1995, 10, 16)
        d3 = Date(2021, 11, 3)
        hash_map = dict()

        hash_map[d1] = 'unit tests'
        self.assertEqual(hash_map[d1], 'unit tests')
        hash_map[d2] = 'jimothy'
        self.assertEqual(hash_map[d2], 'jimothy')
        hash_map[d3] = 'narrows'
        self.assertEqual(hash_map[d3], 'narrows')

        hash_map[d3] = 'success!'
        self.assertEqual(hash_map[d3], 'success!')

        del hash_map[d1]
        with self.assertRaises(KeyError):
            hash_map[d1]

        self.assertIn(d2, hash_map)
        self.assertNotIn(d1, hash_map)
