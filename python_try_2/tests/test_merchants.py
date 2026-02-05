# test_merchants.py

"""Unit tests for the Merchants class.

Last modified 20 Feb 2023 by Greg Vance.
"""


import unittest

from merchants import Merchants, MAX_NUM_MERCHANT_IDS


class TestMerchantsClass(unittest.TestCase):

    def test_Merchants_init(self):
        m = Merchants()
        self.assertEqual(m._names, {})
        self.assertEqual(m._ids, {})

    def test_Merchants_from_file(self):
        # Eventually read a file tests/data/<something> at some point later
        self.assertRaises(NotImplementedError, Merchants.from_file, "mer.txt")

    def test_Merchants_repr(self):
        m = Merchants()
        self.assertEqual(repr(m), "<Merchants object with 0 names and 0 IDs>")
        m.add_merchant("Dunkin' Donuts")
        self.assertEqual(repr(m), "<Merchants object with 1 name and 1 ID>")
        m.add_merchant("Starbucks")
        self.assertEqual(repr(m), "<Merchants object with 2 names and 2 IDs>")
        m.delete_merchant("Dunkin' Donuts")
        self.assertEqual(repr(m), "<Merchants object with 1 name and 1 ID>")
        m.add_nickname("Starbucks", "Sterbusters")
        self.assertEqual(repr(m), "<Merchants object with 2 names and 1 ID>")
        m.add_merchant("Coffee Bean & Tea Leaf")
        self.assertEqual(repr(m), "<Merchants object with 3 names and 2 IDs>")

    def test_Merchants_generate_random_unused_id(self):
        m = Merchants()
        for letter1 in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            for letter2 in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                for letter3 in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    name = letter1 + letter2 + letter3
                    nick1 = name.lower()
                    nick2 = name.title()
                    m.add_merchant(name)
                    m.add_nickname(name, nick1)
                    m.add_nickname(nick1, nick2)

        for _ in range(10 ** 4):
            i = m._generate_random_unused_id()
            self.assertGreaterEqual(i, 0)
            self.assertLess(i, MAX_NUM_MERCHANT_IDS)
            self.assertNotIn(i, m._names.keys())

    def test_Merchants_resolve_to_merchant_id(self):
        m = Merchants()
        m.add_merchant("Belethor's General Goods")
        i = m._ids["Belethor's General Goods"]

        self.assertEqual(
            m._resolve_to_merchant_id("Belethor's General Goods"), i
        )
        self.assertEqual(m._resolve_to_merchant_id(i), i)
        m.add_nickname("Belethor's General Goods", "Belethor's")
        self.assertEqual(m._resolve_to_merchant_id("Belethor's"), i)

        self.assertRaises(KeyError, m._resolve_to_merchant_id, "Whiterun")
        self.assertRaises(KeyError, m._resolve_to_merchant_id, i + 1)

    def test_Merchants_add_merchant(self):
        names = ["Choice Chops", "Commonwealth Weaponry",
                 "Diamond City Surplus", "Chem-I-Care"]
        ids = []
        m = Merchants()

        for name in names:
            m.add_merchant(name)
            self.assertIn(name, m._ids.keys())
            self.assertIn([name], m._names.values())
            i = m._ids[name]
            self.assertIn(i, m._names)
            self.assertEqual(m._names[i], [name])
            self.assertNotIn(i, ids)
            ids.append(i)

        self.assertEqual(len(m._ids), len(names))
        self.assertEqual(len(m._names), len(names))
        self.assertEqual(set(m._ids.keys()), set(names))
        self.assertEqual(set(m._ids.values()), set(ids))
        self.assertEqual(set(m._names.keys()), set(ids))
        self.assertEqual(set(tuple(x) for x in m._names.values()),
                         set((x,) for x in names))

        for name in names:
            self.assertRaises(ValueError, m.add_merchant, name)

    def test_Merchants_add_nickname(self):
        m = Merchants()

        m.add_merchant("Floss")
        m.add_nickname("Floss", "Flossy Dog")
        self.assertIn("Flossy Dog", m._ids.keys())
        self.assertEqual(m._ids["Floss"], m._ids["Flossy Dog"])
        self.assertEqual(m._names[m._ids["Flossy Dog"]],
                         ["Floss", "Flossy Dog"])

        m.add_merchant("Sophie")
        m.add_nickname("Sophie", "Soph-A-Boph")
        m.add_nickname(m._ids["Soph-A-Boph"], "Soph")
        self.assertIn("Soph", m._ids.keys())
        self.assertEqual(m._ids["Sophie"], m._ids["Soph-A-Boph"])
        self.assertEqual(m._ids["Sophie"], m._ids["Soph"])
        self.assertEqual(m._names[m._ids["Soph"]],
                         ["Sophie", "Soph-A-Boph", "Soph"])

        m.add_merchant("Emma")
        m.add_nickname("Emma", "Nemin")
        m.add_nickname("Nemin", "Nems")
        self.assertIn("Nems", m._ids.keys())
        self.assertEqual(m._ids["Emma"], m._ids["Nemin"])
        self.assertEqual(m._ids["Emma"], m._ids["Nems"])
        self.assertEqual(m._names[m._ids["Nems"]],
                         ["Emma", "Nemin", "Nems"])

        self.assertRaises(ValueError, m.add_nickname, "Sophie", "Emma")
        self.assertRaises(ValueError, m.add_nickname, "Floss", "Soph")
        self.assertRaises(ValueError, m.add_nickname,
                          "Flossy Dog", "Soph-A-Boph")
        self.assertRaises(ValueError, m.add_nickname,
                          m._ids["Nemin"], "Nems")

    def test_Merchants_get_merchant_id(self):
        m = Merchants()

        m.add_merchant("Wendy's")
        m.add_merchant("Burger King")
        m.add_nickname("Burger King", "BK")
        m.add_merchant("McDonald's")
        m.add_nickname("McDonald's", "Mickey D's")
        m.add_nickname("Mickey D's", "Mackers")

        i = m.get_merchant_id("Wendy's")
        self.assertEqual(i, m._ids["Wendy's"])
        self.assertEqual(m._names[i], ["Wendy's"])

        i = m.get_merchant_id("Burger King")
        self.assertEqual(i, m._ids["Burger King"])
        self.assertEqual(i, m._ids["BK"])
        self.assertEqual(m._names[i], ["Burger King", "BK"])

        i = m.get_merchant_id("Mickey D's")
        self.assertEqual(i, m._ids["McDonald's"])
        self.assertEqual(i, m._ids["Mickey D's"])
        self.assertEqual(i, m._ids["Mackers"])
        self.assertEqual(m._names[i], ["McDonald's", "Mickey D's", "Mackers"])

        self.assertRaises(KeyError, m.get_merchant_id, "Taco Bell")
        self.assertRaises(KeyError, m.get_merchant_id, "KFC")
        self.assertRaises(KeyError, m.get_merchant_id, "Wendeez")

    def test_Merchants_get_merchant_name(self):
        m = Merchants()
        m.add_merchant("Sagebrush Coffee")
        m.add_nickname("Sagebrush Coffee", "Sagebrush")
        m.add_nickname("Sagebrush", "Saggiebroosh")
        i = m.get_merchant_id("Sagebrush")

        self.assertEqual(
            m.get_merchant_name("Sagebrush Coffee"), "Sagebrush Coffee"
        )
        self.assertEqual(m.get_merchant_name("Sagebrush"), "Sagebrush Coffee")
        self.assertEqual(
            m.get_merchant_name("Saggiebroosh"), "Sagebrush Coffee"
        )
        self.assertEqual(m.get_merchant_name(i), "Sagebrush Coffee")

        self.assertRaises(KeyError, m.get_merchant_name, "Dunkin'")
        self.assertRaises(KeyError, m.get_merchant_name, i + 1)

    def test_Merchants_get_merchant_nicknames(self):
        m = Merchants()
        m.add_merchant("Arizona State University")
        m.add_nickname("Arizona State University", "ASU")
        m.add_nickname("Arizona State University", "Arizona State")
        i1 = m.get_merchant_id("Arizona State University")
        m.add_merchant("Connecticut College")
        m.add_nickname("Connecticut College", "ConnColl")
        m.add_nickname("Connecticut College", "Conn")
        m.add_nickname("Connecticut College", "CC")
        i2 = m.get_merchant_id("Connecticut College")
        m.add_merchant("University of Oxford")
        i3 = m.get_merchant_id("University of Oxford")

        self.assertEqual(
            m.get_merchant_nicknames("Arizona State University"),
            ["ASU", "Arizona State"]
        )
        self.assertEqual(
            m.get_merchant_nicknames("ASU"), ["ASU", "Arizona State"]
        )
        self.assertEqual(
            m.get_merchant_nicknames(i1), ["ASU", "Arizona State"]
        )

        self.assertEqual(
            m.get_merchant_nicknames("Connecticut College"),
            ["ConnColl", "Conn", "CC"]
        )
        self.assertEqual(
            m.get_merchant_nicknames("Conn"), ["ConnColl", "Conn", "CC"]
        )
        self.assertEqual(
            m.get_merchant_nicknames(i2), ["ConnColl", "Conn", "CC"]
        )

        self.assertEqual(m.get_merchant_nicknames("University of Oxford"), [])
        self.assertEqual(m.get_merchant_nicknames(i3), [])
        m.add_nickname(i3, "Oxford")
        self.assertEqual(
            m.get_merchant_nicknames("University of Oxford"), ["Oxford"]
        )
        self.assertEqual(m.get_merchant_nicknames(i3), ["Oxford"])
        self.assertEqual(m.get_merchant_nicknames("Oxford"), ["Oxford"])

        self.assertRaises(KeyError, m.get_merchant_nicknames, "MIT")
        self.assertRaises(KeyError, m.get_merchant_nicknames, "Harvard")

    def test_Merchants_delete_merchant(self):
        m = Merchants()
        m.add_merchant("YouTube")
        m.add_nickname("YouTube", "YT")
        m.add_nickname("YouTube", "The YouToobies")
        i1 = m.get_merchant_id("YouTube")
        m.add_merchant("Facebook")
        m.add_nickname("Facebook", "FB")
        i2 = m.get_merchant_id("Facebook")
        m.add_merchant("Twitter")
        i3 = m.get_merchant_id("Twitter")

        self.assertTrue(m.get_merchant_name(i1) == "YouTube")
        self.assertTrue(m.get_merchant_name(i2) == "Facebook")
        self.assertTrue(m.get_merchant_name(i3) == "Twitter")

        m.delete_merchant("Twitter")
        self.assertRaises(KeyError, m.get_merchant_id, "Twitter")
        self.assertRaises(KeyError, m.get_merchant_name, i3)
        self.assertRaises(KeyError, m.get_merchant_name, "Twitter")
        self.assertRaises(KeyError, m.get_merchant_nicknames, i3)
        self.assertRaises(KeyError, m.get_merchant_nicknames, "Twitter")

        self.assertTrue(m.get_merchant_name(i1) == "YouTube")
        self.assertTrue(m.get_merchant_name(i2) == "Facebook")

        m.delete_merchant("FB")
        self.assertRaises(KeyError, m.get_merchant_id, "Facebook")
        self.assertRaises(KeyError, m.get_merchant_id, "FB")
        self.assertRaises(KeyError, m.get_merchant_name, i2)
        self.assertRaises(KeyError, m.get_merchant_name, "Facebook")
        self.assertRaises(KeyError, m.get_merchant_name, "FB")
        self.assertRaises(KeyError, m.get_merchant_nicknames, i2)
        self.assertRaises(KeyError, m.get_merchant_nicknames, "Facebook")
        self.assertRaises(KeyError, m.get_merchant_nicknames, "FB")

        self.assertTrue(m.get_merchant_name(i1) == "YouTube")

        m.delete_merchant(i1)
        self.assertRaises(KeyError, m.get_merchant_id, "YouTube")
        self.assertRaises(KeyError, m.get_merchant_id, "YT")
        self.assertRaises(KeyError, m.get_merchant_id, "The YouToobies")
        self.assertRaises(KeyError, m.get_merchant_name, i1)
        self.assertRaises(KeyError, m.get_merchant_name, "YouTube")
        self.assertRaises(KeyError, m.get_merchant_name, "YT")
        self.assertRaises(KeyError, m.get_merchant_name, "The YouToobies")
        self.assertRaises(KeyError, m.get_merchant_nicknames, i1)
        self.assertRaises(KeyError, m.get_merchant_nicknames, "YouTube")
        self.assertRaises(KeyError, m.get_merchant_nicknames, "YT")
        self.assertRaises(KeyError, m.get_merchant_nicknames,
                          "The YouToobies")

    def test_Merchants_delete_nickname(self):
        m = Merchants()
        m.add_merchant("Space Miners' Guild")
        m.add_nickname("Space Miners' Guild", "The Guild")
        m.delete_nickname("The Guild")
        self.assertEqual(m.get_merchant_nicknames("Space Miners' Guild"), [])
        self.assertRaises(ValueError, m.delete_nickname, "Space Miners' Guild")
