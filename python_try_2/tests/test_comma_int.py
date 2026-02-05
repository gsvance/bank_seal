# test_comma_int.py

"""Unit tests for the two comma_int functions.

Last modified 9 Feb 2023 by Greg Vance.
"""


import unittest

from comma_int import parse_comma_int, render_comma_int


class TestCommaIntFunctions(unittest.TestCase):

    def test_parse_comma_int_happy(self):
        self.assertEqual(parse_comma_int("0"), 0)
        self.assertEqual(parse_comma_int("-0"), 0)
        self.assertEqual(parse_comma_int("+0"), 0)

        self.assertEqual(parse_comma_int("8"), 8)
        self.assertEqual(parse_comma_int("-2"), -2)
        self.assertEqual(parse_comma_int("+3"), 3)

        self.assertEqual(parse_comma_int("45"), 45)
        self.assertEqual(parse_comma_int("-90"), -90)
        self.assertEqual(parse_comma_int("+97"), 97)

        self.assertEqual(parse_comma_int("761"), 761)
        self.assertEqual(parse_comma_int("-388"), -388)
        self.assertEqual(parse_comma_int("+74"), 74)

        self.assertEqual(parse_comma_int("1,024"), 1024)
        self.assertEqual(parse_comma_int("2048"), 2048)
        self.assertEqual(parse_comma_int("-3,355"), -3355)
        self.assertEqual(parse_comma_int("-5533"), -5533)
        self.assertEqual(parse_comma_int("+5,289"), 5289)
        self.assertEqual(parse_comma_int("+1243"), 1243)

        self.assertEqual(parse_comma_int("65,388"), 65388)
        self.assertEqual(parse_comma_int("54321"), 54321)
        self.assertEqual(parse_comma_int("-25,126"), -25126)
        self.assertEqual(parse_comma_int("-36548"), -36548)
        self.assertEqual(parse_comma_int("+25,289"), 25289)
        self.assertEqual(parse_comma_int("+12643"), 12643)

        self.assertEqual(parse_comma_int("333,444"), 333444)
        self.assertEqual(parse_comma_int("556677"), 556677)
        self.assertEqual(parse_comma_int("-730,123"), -730123)
        self.assertEqual(parse_comma_int("-267922"), -267922)
        self.assertEqual(parse_comma_int("+528,669"), 528669)
        self.assertEqual(parse_comma_int("+812843"), 812843)

        self.assertEqual(parse_comma_int("1,000,456"), 1000456)
        self.assertEqual(parse_comma_int("9753197"), 9753197)
        self.assertEqual(parse_comma_int("-3,644,895"), -3644895)
        self.assertEqual(parse_comma_int("-3225699"), -3225699)
        self.assertEqual(parse_comma_int("+5,289,156"), 5289156)
        self.assertEqual(parse_comma_int("+1243637"), 1243637)

        self.assertEqual(parse_comma_int("23,009,108"), 23009108)
        self.assertEqual(parse_comma_int("44556778"), 44556778)
        self.assertEqual(parse_comma_int("-66,559,874"), -66559874)
        self.assertEqual(parse_comma_int("-15478888"), -15478888)
        self.assertEqual(parse_comma_int("+35,289,156"), 35289156)
        self.assertEqual(parse_comma_int("+71243637"), 71243637)

        self.assertEqual(parse_comma_int("23,009,108"), 23009108)
        self.assertEqual(parse_comma_int("44556778"), 44556778)
        self.assertEqual(parse_comma_int("-232,545,968"), -232545968)
        self.assertEqual(parse_comma_int("-165489512"), -165489512)
        self.assertEqual(parse_comma_int("+365,289,156"), 365289156)
        self.assertEqual(parse_comma_int("+701243637"), 701243637)

    def test_parse_comma_int_pedantry(self):
        err1 = "failed to parse comma-separated int"
        with self.assertRaisesRegex(ValueError, err1):
            parse_comma_int("")
        with self.assertRaisesRegex(ValueError, err1):
            parse_comma_int("1,2")
        with self.assertRaisesRegex(ValueError, err1):
            parse_comma_int(",")
        err2 = "won't parse comma-separated int with leading zero"
        with self.assertRaisesRegex(ValueError, err2):
            parse_comma_int("02,456")
        with self.assertRaisesRegex(ValueError, err2):
            parse_comma_int("00")

    def test_render_comma_int(self):
        self.assertEqual(render_comma_int(0), "0")

        self.assertEqual(render_comma_int(4), "4")
        self.assertEqual(render_comma_int(-8), "-8")
        self.assertEqual(render_comma_int(66), "66")
        self.assertEqual(render_comma_int(-31), "-31")
        self.assertEqual(render_comma_int(458), "458")
        self.assertEqual(render_comma_int(-900), "-900")

        self.assertEqual(render_comma_int(4096), "4,096")
        self.assertEqual(render_comma_int(-2654), "-2,654")
        self.assertEqual(render_comma_int(33256), "33,256")
        self.assertEqual(render_comma_int(-32554), "-32,554")
        self.assertEqual(render_comma_int(445988), "445,988")
        self.assertEqual(render_comma_int(-998775), "-998,775")

        self.assertEqual(render_comma_int(5455977), "5,455,977")
        self.assertEqual(render_comma_int(-1324266), "-1,324,266")
        self.assertEqual(render_comma_int(23009108), "23,009,108")
        self.assertEqual(render_comma_int(-87532786), "-87,532,786")
        self.assertEqual(render_comma_int(978498349), "978,498,349")
        self.assertEqual(render_comma_int(-548937984), "-548,937,984")

    def test_comma_int_round_trips(self):
        integers = [0, 5, -6, 10, -14, 869, -364,
                    8497, -4890, 74784, -98909, 484655, -656456,
                    2256638, -1569348, 16666587, -97889753,
                    978897528, -477292004]
        for i in integers:
            s = render_comma_int(i)
            i2 = parse_comma_int(s)
            self.assertEqual(i2, i)
            s2 = render_comma_int(i2)
            self.assertEqual(s2, s)
