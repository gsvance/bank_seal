# test_money.py

"""Unit tests for the Money class.

Last modified 11 Feb 2023 by Greg Vance.
"""


import unittest

from money import Money


class TestMoneyClass(unittest.TestCase):

    def test_Money_init(self):
        m = Money(0)
        self.assertEqual(m._cents, 0)
        m = Money(899)
        self.assertEqual(m._cents, 899)
        m = Money(-2995)
        self.assertEqual(m._cents, -2995)

    def test_Money_parse_succeeds(self):
        m = Money.parse("2")
        self.assertEqual(m._cents, 200)
        m = Money.parse("$4")
        self.assertEqual(m._cents, 400)
        m = Money.parse("+6")
        self.assertEqual(m._cents, 600)
        m = Money.parse("+$7")
        self.assertEqual(m._cents, 700)
        m = Money.parse("-3")
        self.assertEqual(m._cents, -300)
        m = Money.parse("-$1")
        self.assertEqual(m._cents, -100)

        m = Money.parse("2.")
        self.assertEqual(m._cents, 200)
        m = Money.parse("$4.")
        self.assertEqual(m._cents, 400)
        m = Money.parse("+6.")
        self.assertEqual(m._cents, 600)
        m = Money.parse("+$7.")
        self.assertEqual(m._cents, 700)
        m = Money.parse("-3.")
        self.assertEqual(m._cents, -300)
        m = Money.parse("-$1.")
        self.assertEqual(m._cents, -100)

        m = Money.parse("2.0")
        self.assertEqual(m._cents, 200)
        m = Money.parse("$4.0")
        self.assertEqual(m._cents, 400)
        m = Money.parse("+6.0")
        self.assertEqual(m._cents, 600)
        m = Money.parse("+$7.0")
        self.assertEqual(m._cents, 700)
        m = Money.parse("-3.0")
        self.assertEqual(m._cents, -300)
        m = Money.parse("-$1.0")
        self.assertEqual(m._cents, -100)

        m = Money.parse("2.00")
        self.assertEqual(m._cents, 200)
        m = Money.parse("$4.00")
        self.assertEqual(m._cents, 400)
        m = Money.parse("+6.00")
        self.assertEqual(m._cents, 600)
        m = Money.parse("+$7.00")
        self.assertEqual(m._cents, 700)
        m = Money.parse("-3.00")
        self.assertEqual(m._cents, -300)
        m = Money.parse("-$1.00")
        self.assertEqual(m._cents, -100)

        m = Money.parse("0.02")
        self.assertEqual(m._cents, 2)
        m = Money.parse("$0.04")
        self.assertEqual(m._cents, 4)
        m = Money.parse("+0.06")
        self.assertEqual(m._cents, 6)
        m = Money.parse("+$0.07")
        self.assertEqual(m._cents, 7)
        m = Money.parse("-0.03")
        self.assertEqual(m._cents, -3)
        m = Money.parse("-$0.01")
        self.assertEqual(m._cents, -1)

        m = Money.parse(".02")
        self.assertEqual(m._cents, 2)
        m = Money.parse("$.04")
        self.assertEqual(m._cents, 4)
        m = Money.parse("+.06")
        self.assertEqual(m._cents, 6)
        m = Money.parse("+$.07")
        self.assertEqual(m._cents, 7)
        m = Money.parse("-.03")
        self.assertEqual(m._cents, -3)
        m = Money.parse("-$.01")
        self.assertEqual(m._cents, -1)

        m = Money.parse("0.2")
        self.assertEqual(m._cents, 20)
        m = Money.parse("$0.4")
        self.assertEqual(m._cents, 40)
        m = Money.parse("+0.6")
        self.assertEqual(m._cents, 60)
        m = Money.parse("+$0.7")
        self.assertEqual(m._cents, 70)
        m = Money.parse("-0.3")
        self.assertEqual(m._cents, -30)
        m = Money.parse("-$0.1")
        self.assertEqual(m._cents, -10)

        m = Money.parse("0.20")
        self.assertEqual(m._cents, 20)
        m = Money.parse("$0.40")
        self.assertEqual(m._cents, 40)
        m = Money.parse("+0.60")
        self.assertEqual(m._cents, 60)
        m = Money.parse("+$0.70")
        self.assertEqual(m._cents, 70)
        m = Money.parse("-0.30")
        self.assertEqual(m._cents, -30)
        m = Money.parse("-$0.10")
        self.assertEqual(m._cents, -10)

        m = Money.parse(".20")
        self.assertEqual(m._cents, 20)
        m = Money.parse("$.40")
        self.assertEqual(m._cents, 40)
        m = Money.parse("+.60")
        self.assertEqual(m._cents, 60)
        m = Money.parse("+$.70")
        self.assertEqual(m._cents, 70)
        m = Money.parse("-.30")
        self.assertEqual(m._cents, -30)
        m = Money.parse("-$.10")
        self.assertEqual(m._cents, -10)

        m = Money.parse(".2")
        self.assertEqual(m._cents, 20)
        m = Money.parse("$.4")
        self.assertEqual(m._cents, 40)
        m = Money.parse("+.6")
        self.assertEqual(m._cents, 60)
        m = Money.parse("+$.7")
        self.assertEqual(m._cents, 70)
        m = Money.parse("-.3")
        self.assertEqual(m._cents, -30)
        m = Money.parse("-$.1")
        self.assertEqual(m._cents, -10)

        m = Money.parse("0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("$0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("+0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("+$0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("-0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("-$0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("0.0")
        self.assertEqual(m._cents, 0)
        m = Money.parse(".0")
        self.assertEqual(m._cents, 0)
        m = Money.parse(".00")
        self.assertEqual(m._cents, 0)

        m = Money.parse("8.99")
        self.assertEqual(m._cents, 899)
        m = Money.parse("$4.26")
        self.assertEqual(m._cents, 426)
        m = Money.parse("+4.50")
        self.assertEqual(m._cents, 450)
        m = Money.parse("+$7.45")
        self.assertEqual(m._cents, 745)
        m = Money.parse("-9.04")
        self.assertEqual(m._cents, -904)
        m = Money.parse("-$6.11")
        self.assertEqual(m._cents, -611)

        m = Money.parse(".03")
        self.assertEqual(m._cents, 3)
        m = Money.parse("$.99")
        self.assertEqual(m._cents, 99)
        m = Money.parse("-.87")
        self.assertEqual(m._cents, -87)
        m = Money.parse("-$.72")
        self.assertEqual(m._cents, -72)
        m = Money.parse("+.30")
        self.assertEqual(m._cents, 30)
        m = Money.parse("+$.44")
        self.assertEqual(m._cents, 44)

        m = Money.parse(".3")
        self.assertEqual(m._cents, 30)
        m = Money.parse("$.9")
        self.assertEqual(m._cents, 90)
        m = Money.parse("-.8")
        self.assertEqual(m._cents, -80)
        m = Money.parse("-$.7")
        self.assertEqual(m._cents, -70)
        m = Money.parse("+.0")
        self.assertEqual(m._cents, 0)
        m = Money.parse("+$.4")
        self.assertEqual(m._cents, 40)

    def test_Money_parse_fails(self):
        rubbish_bin = [
            "", " ", "$", "+", "-", "+$", "-$", ".", "$.",
            "1.2.3", ",,,", ",,.4,5", "45.5,6", "$4,5.32",
            "$-4", "$+3", "$+56.01", "$-31.4", "$1.012"
        ]
        for rubbish in rubbish_bin:
            self.assertRaises(ValueError, Money.parse, rubbish)

    def test_Money_from_numeric(self):
        m = Money.from_numeric(19.99)
        self.assertEqual(m._cents, 1999)
        m = Money.from_numeric(.1)
        self.assertEqual(m._cents, 10)
        m = Money.from_numeric(556)
        self.assertEqual(m._cents, 55600)
        m = Money.from_numeric(-295.31)
        self.assertEqual(m._cents, -29531)
        m = Money.from_numeric(7 + 1e-4, picky=False)
        self.assertEqual(m._cents, 700)
        m = Money.from_numeric(-1.058, picky=False)
        self.assertEqual(m._cents, -106)

        err = "cannot convert .+ to Money with picky=True"
        with self.assertRaisesRegex(ValueError, err):
            m = Money.from_numeric(6.751)

    def test_Money_str(self):
        self.assertEqual(str(Money(0)), "$0.00")
        self.assertEqual(str(Money(8)), "$0.08")
        self.assertEqual(str(Money(-2)), "-$0.02")
        self.assertEqual(str(Money(40)), "$0.40")
        self.assertEqual(str(Money(-90)), "-$0.90")
        self.assertEqual(str(Money(14)), "$0.14")
        self.assertEqual(str(Money(-65)), "-$0.65")

        self.assertEqual(str(Money(200)), "$2.00")
        self.assertEqual(str(Money(-900)), "-$9.00")
        self.assertEqual(str(Money(307)), "$3.07")
        self.assertEqual(str(Money(-401)), "-$4.01")
        self.assertEqual(str(Money(530)), "$5.30")
        self.assertEqual(str(Money(-620)), "-$6.20")
        self.assertEqual(str(Money(755)), "$7.55")
        self.assertEqual(str(Money(-892)), "-$8.92")

        self.assertEqual(str(Money(4567)), "$45.67")
        self.assertEqual(str(Money(-7590)), "-$75.90")
        self.assertEqual(str(Money(19407)), "$194.07")
        self.assertEqual(str(Money(-98510)), "-$985.10")
        self.assertEqual(str(Money(841000)), "$8,410.00")
        self.assertEqual(str(Money(-940281)), "-$9,402.81")
        self.assertEqual(str(Money(7593765)), "$75,937.65")
        self.assertEqual(str(Money(-5884967)), "-$58,849.67")

    def test_Money_repr(self):
        self.assertEqual(repr(Money(0)), "Money(0)")
        self.assertEqual(repr(Money(4567)), "Money(4567)")
        self.assertEqual(repr(Money(-98510)), "Money(-98510)")

    def test_Money_sign(self):
        m = Money(8923)
        self.assertEqual(m.sign, +1)
        m = Money(-36)
        self.assertEqual(m.sign, -1)
        m = Money(0)
        self.assertEqual(m.sign, 0)

    def test_Money_unsigned_dollars(self):
        m = Money(24689)
        self.assertEqual(m.unsigned_dollars, 246)
        m = Money(71)
        self.assertEqual(m.unsigned_dollars, 0)
        m = Money(500)
        self.assertEqual(m.unsigned_dollars, 5)
        m = Money(-985)
        self.assertEqual(m.unsigned_dollars, 9)
        m = Money(-6)
        self.assertEqual(m.unsigned_dollars, 0)
        m = Money(-1000)
        self.assertEqual(m.unsigned_dollars, 10)
        m = Money(0)
        self.assertEqual(m.unsigned_dollars, 0)

    def test_Money_unsigned_cents(self):
        m = Money(24689)
        self.assertEqual(m.unsigned_cents, 89)
        m = Money(71)
        self.assertEqual(m.unsigned_cents, 71)
        m = Money(500)
        self.assertEqual(m.unsigned_cents, 0)
        m = Money(-985)
        self.assertEqual(m.unsigned_cents, 85)
        m = Money(-6)
        self.assertEqual(m.unsigned_cents, 6)
        m = Money(-1000)
        self.assertEqual(m.unsigned_cents, 0)
        m = Money(0)
        self.assertEqual(m.unsigned_cents, 0)

    def test_Money_in_pennies(self):
        m = Money(0)
        self.assertEqual(m.in_pennies, 0)
        m = Money(2647)
        self.assertEqual(m.in_pennies, 2647)
        m = Money(-95743)
        self.assertEqual(m.in_pennies, -95743)

    def test_Money_float(self):
        f = float(Money(0))
        self.assertEqual(f, 0.0)
        f = float(Money(43))
        self.assertEqual(f, 0.43)
        f = float(Money(9521))
        self.assertEqual(f, 95.21)
        f = float(Money(-7800))
        self.assertEqual(f, -78.0)
        f = float(Money(-264789412))
        self.assertEqual(f, -2647894.12)

    def test_Money_int(self):
        i = int(Money(0))
        self.assertEqual(i, 0)
        i = int(Money(43))
        self.assertEqual(i, 0)
        i = int(Money(9521))
        self.assertEqual(i, 95)
        i = int(Money(-7800))
        self.assertEqual(i, -78)
        i = int(Money(-264789412))
        self.assertEqual(i, -2647894)

    def test_Money_bool(self):
        self.assertFalse(Money(0))
        self.assertTrue(Money(452))
        self.assertTrue(Money(-100))

    def test_Money_compare(self):
        m = Money(405)

        self.assertEqual(m._compare(Money(398)), 7)
        self.assertEqual(m._compare(3.91), 14)
        self.assertEqual(m._compare(2), 205)

        self.assertEqual(m._compare(Money(500)), -95)
        self.assertEqual(m._compare(4.50), -45)
        self.assertEqual(m._compare(6), -195)

        self.assertEqual(m._compare(Money(405)), 0)
        self.assertEqual(m._compare(4.05), 0)

    def test_Money_comparisons(self):
        m1 = Money(-1299)
        m2 = Money(-75)
        m3 = Money(-75)
        m4 = Money(0)
        m5 = Money(512)

        self.assertLess(m1, m5)
        self.assertFalse(m1 >= m5)
        self.assertLess(m2, m4)
        self.assertFalse(m2 >= m4)

        self.assertLessEqual(m2, m3)
        self.assertFalse(m2 > m3)
        self.assertLessEqual(m1, m4)
        self.assertFalse(m1 > m4)

        self.assertEqual(m2, m3)
        self.assertFalse(m2 != m3)
        self.assertNotEqual(m4, m5)
        self.assertFalse(m4 == m5)

        self.assertGreater(m2, m1)
        self.assertFalse(m2 <= m1)
        self.assertGreater(m4, m3)
        self.assertFalse(m4 <= m3)

        self.assertGreaterEqual(m3, m2)
        self.assertFalse(m3 < m2)
        self.assertGreaterEqual(m5, m1)
        self.assertFalse(m5 < m1)

    def test_Money_unary_operations(self):
        m1 = Money(0)
        m2 = Money(4542)
        m3 = Money(-473)

        self.assertEqual(+m1, Money(0))
        self.assertEqual(+m2, Money(4542))
        self.assertEqual(+m3, Money(-473))

        self.assertEqual(-m1, Money(0))
        self.assertEqual(-m2, Money(-4542))
        self.assertEqual(-m3, Money(473))

        self.assertEqual(abs(m1), Money(0))
        self.assertEqual(abs(m2), Money(4542))
        self.assertEqual(abs(m3), Money(473))

    def test_Money_addition(self):
        m0 = Money(0)
        m1 = Money(905)
        m2 = Money(-63)

        self.assertEqual(m0 + m1, m1)
        self.assertEqual(m1 + m0, m1)
        self.assertEqual(m0 + m2, m2)
        self.assertEqual(m2 + m0, m2)
        self.assertEqual(m1 + m2, Money(842))
        self.assertEqual(m2 + m1, Money(842))

        self.assertEqual(m0 + 2, Money(200))
        self.assertEqual(m1 + 10, Money(1905))
        self.assertEqual(m2 + 4, Money(337))
        self.assertEqual(61 + m0, Money(6100))
        self.assertEqual(8 + m1, Money(1705))
        self.assertEqual(40 + m2, Money(3937))

        self.assertEqual(m0 + (-3), Money(-300))
        self.assertEqual(m1 + (-6), Money(305))
        self.assertEqual(m2 + (-2), Money(-263))
        self.assertEqual((-13) + m0, Money(-1300))
        self.assertEqual((-11) + m1, Money(-195))
        self.assertEqual((-20) + m2, Money(-2063))

        self.assertEqual(m0 + 83.9, Money(8390))
        self.assertEqual(m1 + 3.06, Money(1211))
        self.assertEqual(m2 + .2, Money(-43))
        self.assertEqual(6.79 + m0, Money(679))
        self.assertEqual(11. + m1, Money(2005))
        self.assertEqual(1.27 + m2, Money(64))

        self.assertEqual(m0 + (-2.5), Money(-250))
        self.assertEqual(m1 + (-9.15), Money(-10))
        self.assertEqual(m2 + (-500.3), Money(-50093))
        self.assertEqual((-1099.95) + m0, Money(-109995))
        self.assertEqual((-86.44) + m1, Money(-7739))
        self.assertEqual((-2.34) + m2, Money(-297))

    def test_Money_subtraction(self):
        m0 = Money(0)
        m1 = Money(1020)
        m2 = Money(-4)

        self.assertEqual(m0 - m1, Money(-1020))
        self.assertEqual(m1 - m0, m1)
        self.assertEqual(m0 - m2, Money(4))
        self.assertEqual(m2 - m0, m2)
        self.assertEqual(m1 - m2, Money(1024))
        self.assertEqual(m2 - m1, Money(-1024))

        self.assertEqual(m0 - 1, Money(-100))
        self.assertEqual(m1 - 8, Money(220))
        self.assertEqual(m2 - 4, Money(-404))
        self.assertEqual(60 - m0, Money(6000))
        self.assertEqual(18 - m1, Money(780))
        self.assertEqual(30 - m2, Money(3004))

        self.assertEqual(m0 - (-5), Money(500))
        self.assertEqual(m1 - (-7), Money(1720))
        self.assertEqual(m2 - (-1), Money(96))
        self.assertEqual((-34) - m0, Money(-3400))
        self.assertEqual((-22) - m1, Money(-3220))
        self.assertEqual((-28) - m2, Money(-2796))

        self.assertEqual(m0 - 68.04, Money(-6804))
        self.assertEqual(m1 - 3.1, Money(710))
        self.assertEqual(m2 - .7, Money(-74))
        self.assertEqual(0.54 - m0, Money(54))
        self.assertEqual(14.0 - m1, Money(380))
        self.assertEqual(2.73 - m2, Money(277))

        self.assertEqual(m0 - (-3.3), Money(330))
        self.assertEqual(m1 - (-98.10), Money(10830))
        self.assertEqual(m2 - (-460.8), Money(46076))
        self.assertEqual((-4055.32) - m0, Money(-405532))
        self.assertEqual((-49.37) - m1, Money(-5957))
        self.assertEqual((-7.43) - m2, Money(-739))

    def test_Money_multiplication(self):
        m0 = Money(0)
        m1 = Money(25)
        m2 = Money(-310)

        self.assertEqual(m0 * 4, m0)
        self.assertEqual(m1 * 0, m0)
        self.assertEqual(m2 * 0, m0)
        self.assertEqual(5 * m0, m0)
        self.assertEqual(0 * m1, m0)
        self.assertEqual(0 * m2, m0)

        self.assertEqual(m1 * 8, Money(200))
        self.assertEqual(m2 * 3, Money(-930))
        self.assertEqual(m1 * -110, Money(-2750))
        self.assertEqual(m2 * -4, Money(1240))

    def test_Money_augmented_assignment(self):
        m = Money(-100)
        m += Money(3)
        self.assertEqual(m, Money(-97))
        m += 2
        self.assertEqual(m, Money(103))
        m += 4.56
        self.assertEqual(m, Money(559))
        m += Money(-509)
        self.assertEqual(m, Money(50))
        m += (-2)
        self.assertEqual(m, Money(-150))
        m += (-2.54)
        self.assertEqual(m, Money(-404))

        m = Money(200)
        m -= Money(40)
        self.assertEqual(m, Money(160))
        m -= 1
        self.assertEqual(m, Money(60))
        m -= 2.70
        self.assertEqual(m, Money(-210))
        m -= Money(-105)
        self.assertEqual(m, Money(-105))
        m -= (-4)
        self.assertEqual(m, Money(295))
        m -= (-1.33)
        self.assertEqual(m, Money(428))

        m = Money(200)
        m *= 7
        self.assertEqual(m, Money(1400))
        m *= (-3)
        self.assertEqual(m, Money(-4200))
        m *= 2
        self.assertEqual(m, Money(-8400))
        m *= (-10)
        self.assertEqual(m, Money(84000))

    def test_Money_hash(self):
        m1 = Money(1999)
        m2 = Money(500)
        m3 = Money(-3078)
        hash_map = dict()

        hash_map[m1] = 'blender'
        self.assertEqual(hash_map[m1], 'blender')
        self.assertEqual(hash_map[19.99], 'blender')
        hash_map[m2] = 'five bucks'
        self.assertEqual(hash_map[m2], 'five bucks')
        self.assertEqual(hash_map[5], 'five bucks')
        self.assertEqual(hash_map[5.0], 'five bucks')
        hash_map[m3] = 'fee'
        self.assertEqual(hash_map[m3], 'fee')
        self.assertEqual(hash_map[-30.78], 'fee')

        hash_map[-30.78] = 'refund!'
        self.assertEqual(hash_map[m3], 'refund!')
        self.assertEqual(hash_map[-30.78], 'refund!')

        self.assertIn(m1, hash_map)
        self.assertIn(19.99, hash_map)
        self.assertIn(m2, hash_map)
        self.assertIn(5, hash_map)
        self.assertIn(5.00, hash_map)
        self.assertIn(m3, hash_map)
        self.assertIn(-30.78, hash_map)

        self.assertNotIn(20, hash_map)
        self.assertNotIn(19.9901, hash_map)

        del hash_map[m1]
        with self.assertRaises(KeyError):
            hash_map[m1]
        self.assertNotIn(m1, hash_map)
        with self.assertRaises(KeyError):
            hash_map[19.99]
        self.assertNotIn(19.99, hash_map)

        del hash_map[5]
        with self.assertRaises(KeyError):
            hash_map[m2]
        self.assertNotIn(m2, hash_map)
        with self.assertRaises(KeyError):
            hash_map[5.0]
        self.assertNotIn(5.0, hash_map)
        with self.assertRaises(KeyError):
            hash_map[5]
        self.assertNotIn(5, hash_map)

        del hash_map[-30.78]
        with self.assertRaises(KeyError):
            hash_map[m3]
        self.assertNotIn(m3, hash_map)
        with self.assertRaises(KeyError):
            hash_map[-30.78]
        self.assertNotIn(-30.78, hash_map)

        self.assertEqual(hash_map, {})

        hash_map[10] = 'ten bucks'
        hash_map[50.0] = 'fifty bucks'
        self.assertEqual(hash_map[Money(1000)], 'ten bucks')
        self.assertEqual(hash_map[Money(5000)], 'fifty bucks')
