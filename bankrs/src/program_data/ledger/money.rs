use std::cmp::Ordering;
use std::convert::From;
use std::error::Error;
use std::fmt::{self, Display};
use std::num::ParseIntError;
use std::ops;
use std::str::FromStr;

use lazy_static;
use regex::Regex;
use serde::{Deserialize, Serialize};

use super::comma_int::{parse_comma_int, render_comma_int, CommaIntError};

const DOLLAR_CENTS: i64 = 100; // Number of cents in one dollar
const DIME_CENTS: i64 = 10; // Number of cents in one dime

lazy_static::lazy_static! {
    static ref MONEY_FORMAT: Regex = Regex::new(r"(?x)
        \A\s*            # Optional whitespace at start
        (?P<sign>[-+]?)  # then an optional +/- sign
        \$?              # and an optional $ before any digits
        (?P<dollars>     # The integer dollars part consists of
            [\d,]*       # a (possibly empty) string of digits and commas
                         # which greedy-matches as much as possible
        ) \.?            # and ends if we hit a decimal point
        (?P<cents>       # If any more digits are left
            \d{0,2}      # then match at most two as the cents part
        )
        \s*\z            # More optional whitespace at end
    ").expect("MONEY_FORMAT regex should compile without issues");
}

#[derive(Debug)]
pub enum MoneyError {
    FormatFailure(String),
    PickyProblem(f64),
    CommaParseError(CommaIntError),
    IntParseError(ParseIntError),
}

impl Display for MoneyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::FormatFailure(string) => {
                write!(f, "incorrect format for money: {:?}", string)
            }
            Self::PickyProblem(float) => {
                write!(f, "cannot convert {:?} to money when picky", float)
            }
            Self::CommaParseError(error) => {
                write!(f, "{}", error)
            }
            Self::IntParseError(error) => {
                write!(f, "{}", error)
            }
        }
    }
}

impl Error for MoneyError {}

#[derive(Debug, Clone, Copy, PartialOrd, Ord, PartialEq, Eq, Hash, Deserialize, Serialize)]
pub struct Money {
    cents: i64,
}

impl Money {
    pub fn new(cents: i64) -> Self {
        Self { cents }
    }
}

impl FromStr for Money {
    type Err = MoneyError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let captures = match MONEY_FORMAT.captures(s) {
            Some(captures) => captures,
            None => return Err(MoneyError::FormatFailure(s.to_owned())),
        };

        // The MONEY_FORMAT regex *technically* allows strings like "$."
        // Rather than calling a string with no digits zero, call it an error
        let has_digits = captures
            .get(0)
            .expect("group 0 is guaranteed to be valid")
            .as_str()
            .chars()
            .any(|ch| ch.is_ascii_digit());
        if !has_digits {
            return Err(MoneyError::FormatFailure(s.to_owned()));
        }

        let sign = captures
            .name("sign")
            .expect("named group 'sign' should be valid if regex matches")
            .as_str();

        let dollars = captures
            .name("dollars")
            .expect("named group 'dollars' should be valid if regex matches")
            .as_str();
        let dollars = match parse_comma_int(dollars) {
            Ok(integer) => integer,
            Err(_) if dollars == "" => 0,
            Err(error) => return Err(MoneyError::CommaParseError(error)),
        };

        let cents = captures
            .name("cents")
            .expect("named group 'cents' should be valid if regex matches")
            .as_str();
        let cents: i64 = match cents.parse() {
            Ok(integer) if cents.len() == 1 => integer * DIME_CENTS,
            Ok(integer) => integer,
            Err(_) if cents == "" => 0,
            Err(error) => return Err(MoneyError::IntParseError(error)),
        };

        if sign == "-" {
            Ok(Self::new(-dollars * DOLLAR_CENTS - cents))
        } else {
            Ok(Self::new(dollars * DOLLAR_CENTS + cents))
        }
    }
}

impl From<i64> for Money {
    fn from(value: i64) -> Self {
        Self::new(value * DOLLAR_CENTS)
    }
}

impl Money {
    /// Interpret a numeric type as Money by rounding to the nearest cent.
    ///
    /// Construct a new Money struct whose value in dollars and cents is given
    /// by the float n. If picky is true, then the input *must* be as near as
    /// possible to an exact multiple of 1 cent, such that
    ///     f64::from(Money::from_numeric(n, true).unwrap()) == n.
    /// If picky is false, then the input is simply rounded to the nearest cent
    /// without regard for whether the conversion is reversible.
    pub fn from_numeric(n: f64, picky: bool) -> Result<Self, MoneyError> {
        let rounded = (n * DOLLAR_CENTS as f64).round();
        let money = Money::new(rounded as i64);

        if !picky || f64::from(money) == n {
            Ok(money)
        } else {
            Err(MoneyError::PickyProblem(n))
        }
    }
}

impl Money {
    pub fn sign(&self) -> i64 {
        match self.cents.cmp(&0) {
            Ordering::Greater => 1,
            Ordering::Less => -1,
            Ordering::Equal => 0,
        }
    }

    pub fn absolute_dollars(&self) -> i64 {
        self.cents.abs() / DOLLAR_CENTS
    }

    pub fn absolute_cents(&self) -> i64 {
        self.cents.abs() % DOLLAR_CENTS
    }

    pub fn in_pennies(&self) -> i64 {
        self.cents
    }
}

impl Display for Money {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let sign = if self.sign() == -1 { "-" } else { "" };
        let dollars = render_comma_int(self.absolute_dollars());
        let cents = format!("{:0>2}", self.absolute_cents());
        write!(f, "{}${}.{}", sign, dollars, cents)
    }
}

impl From<Money> for f64 {
    fn from(value: Money) -> f64 {
        (value.in_pennies() as f64) / (DOLLAR_CENTS as f64)
    }
}

impl From<Money> for i64 {
    fn from(value: Money) -> i64 {
        if value.in_pennies() >= 0 {
            // Floor positive numbers towards zero
            value.in_pennies() / DOLLAR_CENTS
        } else {
            // Ceil negative numbers towards zero
            -(-value.in_pennies() / DOLLAR_CENTS)
        }
    }
}

impl From<Money> for bool {
    fn from(value: Money) -> bool {
        value.in_pennies() != 0
    }
}

impl ops::Neg for Money {
    type Output = Self;

    fn neg(self) -> Self::Output {
        Self::new(-self.cents)
    }
}

impl Money {
    pub fn abs(self) -> Self {
        Self::new(self.cents.abs())
    }
}

impl ops::Add for Money {
    type Output = Self;

    fn add(self, rhs: Self) -> Self::Output {
        Self::new(self.cents + rhs.cents)
    }
}

impl ops::Sub for Money {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self::Output {
        self + -rhs
    }
}

impl ops::Mul<i64> for Money {
    type Output = Self;

    fn mul(self, rhs: i64) -> Self::Output {
        Self::new(self.cents * rhs)
    }
}

impl ops::Mul<Money> for i64 {
    type Output = Money;

    fn mul(self, rhs: Money) -> Self::Output {
        rhs * self
    }
}

impl ops::AddAssign for Money {
    fn add_assign(&mut self, rhs: Self) {
        self.cents += rhs.cents
    }
}

impl ops::SubAssign for Money {
    fn sub_assign(&mut self, rhs: Self) {
        self.cents -= rhs.cents
    }
}

impl ops::MulAssign<i64> for Money {
    fn mul_assign(&mut self, rhs: i64) {
        self.cents *= rhs
    }
}

#[cfg(test)]
mod test_money {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn new() {
        let m = Money::new(0);
        assert_eq!(m.cents, 0);
        let m = Money::new(899);
        assert_eq!(m.cents, 899);
        let m = Money::new(-2995);
        assert_eq!(m.cents, -2995);
    }

    #[test]
    fn parse_succeeds() {
        let m: Money = "2".parse().unwrap();
        assert_eq!(m.cents, 200);
        let m: Money = "$4".parse().unwrap();
        assert_eq!(m.cents, 400);
        let m: Money = "+6".parse().unwrap();
        assert_eq!(m.cents, 600);
        let m: Money = "+$7".parse().unwrap();
        assert_eq!(m.cents, 700);
        let m: Money = "-3".parse().unwrap();
        assert_eq!(m.cents, -300);
        let m: Money = "-$1".parse().unwrap();
        assert_eq!(m.cents, -100);

        let m: Money = "2.".parse().unwrap();
        assert_eq!(m.cents, 200);
        let m: Money = "$4.".parse().unwrap();
        assert_eq!(m.cents, 400);
        let m: Money = "+6.".parse().unwrap();
        assert_eq!(m.cents, 600);
        let m: Money = "+$7.".parse().unwrap();
        assert_eq!(m.cents, 700);
        let m: Money = "-3.".parse().unwrap();
        assert_eq!(m.cents, -300);
        let m: Money = "-$1.".parse().unwrap();
        assert_eq!(m.cents, -100);

        let m: Money = "2.0".parse().unwrap();
        assert_eq!(m.cents, 200);
        let m: Money = "$4.0".parse().unwrap();
        assert_eq!(m.cents, 400);
        let m: Money = "+6.0".parse().unwrap();
        assert_eq!(m.cents, 600);
        let m: Money = "+$7.0".parse().unwrap();
        assert_eq!(m.cents, 700);
        let m: Money = "-3.0".parse().unwrap();
        assert_eq!(m.cents, -300);
        let m: Money = "-$1.0".parse().unwrap();
        assert_eq!(m.cents, -100);

        let m: Money = "2.00".parse().unwrap();
        assert_eq!(m.cents, 200);
        let m: Money = "$4.00".parse().unwrap();
        assert_eq!(m.cents, 400);
        let m: Money = "+6.00".parse().unwrap();
        assert_eq!(m.cents, 600);
        let m: Money = "+$7.00".parse().unwrap();
        assert_eq!(m.cents, 700);
        let m: Money = "-3.00".parse().unwrap();
        assert_eq!(m.cents, -300);
        let m: Money = "-$1.00".parse().unwrap();
        assert_eq!(m.cents, -100);

        let m: Money = "0.02".parse().unwrap();
        assert_eq!(m.cents, 2);
        let m: Money = "$0.04".parse().unwrap();
        assert_eq!(m.cents, 4);
        let m: Money = "+0.06".parse().unwrap();
        assert_eq!(m.cents, 6);
        let m: Money = "+$0.07".parse().unwrap();
        assert_eq!(m.cents, 7);
        let m: Money = "-0.03".parse().unwrap();
        assert_eq!(m.cents, -3);
        let m: Money = "-$0.01".parse().unwrap();
        assert_eq!(m.cents, -1);

        let m: Money = ".02".parse().unwrap();
        assert_eq!(m.cents, 2);
        let m: Money = "$.04".parse().unwrap();
        assert_eq!(m.cents, 4);
        let m: Money = "+.06".parse().unwrap();
        assert_eq!(m.cents, 6);
        let m: Money = "+$.07".parse().unwrap();
        assert_eq!(m.cents, 7);
        let m: Money = "-.03".parse().unwrap();
        assert_eq!(m.cents, -3);
        let m: Money = "-$.01".parse().unwrap();
        assert_eq!(m.cents, -1);

        let m: Money = "0.2".parse().unwrap();
        assert_eq!(m.cents, 20);
        let m: Money = "$0.4".parse().unwrap();
        assert_eq!(m.cents, 40);
        let m: Money = "+0.6".parse().unwrap();
        assert_eq!(m.cents, 60);
        let m: Money = "+$0.7".parse().unwrap();
        assert_eq!(m.cents, 70);
        let m: Money = "-0.3".parse().unwrap();
        assert_eq!(m.cents, -30);
        let m: Money = "-$0.1".parse().unwrap();
        assert_eq!(m.cents, -10);

        let m: Money = "0.20".parse().unwrap();
        assert_eq!(m.cents, 20);
        let m: Money = "$0.40".parse().unwrap();
        assert_eq!(m.cents, 40);
        let m: Money = "+0.60".parse().unwrap();
        assert_eq!(m.cents, 60);
        let m: Money = "+$0.70".parse().unwrap();
        assert_eq!(m.cents, 70);
        let m: Money = "-0.30".parse().unwrap();
        assert_eq!(m.cents, -30);
        let m: Money = "-$0.10".parse().unwrap();
        assert_eq!(m.cents, -10);

        let m: Money = ".20".parse().unwrap();
        assert_eq!(m.cents, 20);
        let m: Money = "$.40".parse().unwrap();
        assert_eq!(m.cents, 40);
        let m: Money = "+.60".parse().unwrap();
        assert_eq!(m.cents, 60);
        let m: Money = "+$.70".parse().unwrap();
        assert_eq!(m.cents, 70);
        let m: Money = "-.30".parse().unwrap();
        assert_eq!(m.cents, -30);
        let m: Money = "-$.10".parse().unwrap();
        assert_eq!(m.cents, -10);

        let m: Money = ".2".parse().unwrap();
        assert_eq!(m.cents, 20);
        let m: Money = "$.4".parse().unwrap();
        assert_eq!(m.cents, 40);
        let m: Money = "+.6".parse().unwrap();
        assert_eq!(m.cents, 60);
        let m: Money = "+$.7".parse().unwrap();
        assert_eq!(m.cents, 70);
        let m: Money = "-.3".parse().unwrap();
        assert_eq!(m.cents, -30);
        let m: Money = "-$.1".parse().unwrap();
        assert_eq!(m.cents, -10);

        let m: Money = "0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "$0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "+0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "+$0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "-0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "-$0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "0.0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = ".0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = ".00".parse().unwrap();
        assert_eq!(m.cents, 0);

        let m: Money = "8.99".parse().unwrap();
        assert_eq!(m.cents, 899);
        let m: Money = "$4.26".parse().unwrap();
        assert_eq!(m.cents, 426);
        let m: Money = "+4.50".parse().unwrap();
        assert_eq!(m.cents, 450);
        let m: Money = "+$7.45".parse().unwrap();
        assert_eq!(m.cents, 745);
        let m: Money = "-9.04".parse().unwrap();
        assert_eq!(m.cents, -904);
        let m: Money = "-$6.11".parse().unwrap();
        assert_eq!(m.cents, -611);

        let m: Money = ".03".parse().unwrap();
        assert_eq!(m.cents, 3);
        let m: Money = "$.99".parse().unwrap();
        assert_eq!(m.cents, 99);
        let m: Money = "-.87".parse().unwrap();
        assert_eq!(m.cents, -87);
        let m: Money = "-$.72".parse().unwrap();
        assert_eq!(m.cents, -72);
        let m: Money = "+.30".parse().unwrap();
        assert_eq!(m.cents, 30);
        let m: Money = "+$.44".parse().unwrap();
        assert_eq!(m.cents, 44);

        let m: Money = ".3".parse().unwrap();
        assert_eq!(m.cents, 30);
        let m: Money = "$.9".parse().unwrap();
        assert_eq!(m.cents, 90);
        let m: Money = "-.8".parse().unwrap();
        assert_eq!(m.cents, -80);
        let m: Money = "-$.7".parse().unwrap();
        assert_eq!(m.cents, -70);
        let m: Money = "+.0".parse().unwrap();
        assert_eq!(m.cents, 0);
        let m: Money = "+$.4".parse().unwrap();
        assert_eq!(m.cents, 40);
    }

    #[test]
    fn parse_fails() {
        let rubbish_bin = [
            "", " ", "$", "+", "-", "+$", "-$", ".", "$.", "1.2.3", ",,,", ",,.4,5", "45.5,6",
            "$4,5.32", "$-4", "$+3", "$+56.01", "$-31.4", "$1.012",
        ];
        for rubbish in rubbish_bin {
            assert!(rubbish.parse::<Money>().is_err());
        }
    }

    #[test]
    fn from_i64_and_from_numeric() {
        let m = Money::from_numeric(19.99, true).unwrap();
        assert_eq!(m.cents, 1999);
        let m = Money::from_numeric(0.1, true).unwrap();
        assert_eq!(m.cents, 10);
        let m = Money::from(556);
        assert_eq!(m.cents, 55600);
        let m = Money::from_numeric(-295.31, true).unwrap();
        assert_eq!(m.cents, -29531);
        let m = Money::from_numeric(7. + 1e-4, false).unwrap();
        assert_eq!(m.cents, 700);
        let m = Money::from_numeric(-1.058, false).unwrap();
        assert_eq!(m.cents, -106);

        assert!(Money::from_numeric(6.751, true).is_err());
    }

    #[test]
    fn display() {
        assert_eq!(Money::new(0).to_string(), "$0.00");
        assert_eq!(Money::new(8).to_string(), "$0.08");
        assert_eq!(Money::new(-2).to_string(), "-$0.02");
        assert_eq!(Money::new(40).to_string(), "$0.40");
        assert_eq!(Money::new(-90).to_string(), "-$0.90");
        assert_eq!(Money::new(14).to_string(), "$0.14");
        assert_eq!(Money::new(-65).to_string(), "-$0.65");

        assert_eq!(Money::new(200).to_string(), "$2.00");
        assert_eq!(Money::new(-900).to_string(), "-$9.00");
        assert_eq!(Money::new(307).to_string(), "$3.07");
        assert_eq!(Money::new(-401).to_string(), "-$4.01");
        assert_eq!(Money::new(530).to_string(), "$5.30");
        assert_eq!(Money::new(-620).to_string(), "-$6.20");
        assert_eq!(Money::new(755).to_string(), "$7.55");
        assert_eq!(Money::new(-892).to_string(), "-$8.92");

        assert_eq!(Money::new(4567).to_string(), "$45.67");
        assert_eq!(Money::new(-7590).to_string(), "-$75.90");
        assert_eq!(Money::new(19407).to_string(), "$194.07");
        assert_eq!(Money::new(-98510).to_string(), "-$985.10");
        assert_eq!(Money::new(841000).to_string(), "$8,410.00");
        assert_eq!(Money::new(-940281).to_string(), "-$9,402.81");
        assert_eq!(Money::new(7593765).to_string(), "$75,937.65");
        assert_eq!(Money::new(-5884967).to_string(), "-$58,849.67");
    }

    #[test]
    fn debug() {
        assert_eq!(format!("{:?}", Money::new(0)), "Money { cents: 0 }");
        assert_eq!(format!("{:?}", Money::new(4567)), "Money { cents: 4567 }");
        assert_eq!(
            format!("{:?}", Money::new(-98510)),
            "Money { cents: -98510 }"
        );
    }

    #[test]
    fn sign() {
        let m = Money::new(8923);
        assert_eq!(m.sign(), 1);
        let m = Money::new(-36);
        assert_eq!(m.sign(), -1);
        let m = Money::new(0);
        assert_eq!(m.sign(), 0);
    }

    #[test]
    fn absolute_dollars() {
        let m = Money::new(24689);
        assert_eq!(m.absolute_dollars(), 246);
        let m = Money::new(71);
        assert_eq!(m.absolute_dollars(), 0);
        let m = Money::new(500);
        assert_eq!(m.absolute_dollars(), 5);
        let m = Money::new(-985);
        assert_eq!(m.absolute_dollars(), 9);
        let m = Money::new(-6);
        assert_eq!(m.absolute_dollars(), 0);
        let m = Money::new(-1000);
        assert_eq!(m.absolute_dollars(), 10);
        let m = Money::new(0);
        assert_eq!(m.absolute_dollars(), 0);
    }

    #[test]
    fn absolute_cents() {
        let m = Money::new(24689);
        assert_eq!(m.absolute_cents(), 89);
        let m = Money::new(71);
        assert_eq!(m.absolute_cents(), 71);
        let m = Money::new(500);
        assert_eq!(m.absolute_cents(), 0);
        let m = Money::new(-985);
        assert_eq!(m.absolute_cents(), 85);
        let m = Money::new(-6);
        assert_eq!(m.absolute_cents(), 6);
        let m = Money::new(-1000);
        assert_eq!(m.absolute_cents(), 0);
        let m = Money::new(0);
        assert_eq!(m.absolute_cents(), 0);
    }

    #[test]
    fn in_pennies() {
        let m = Money::new(0);
        assert_eq!(m.in_pennies(), 0);
        let m = Money::new(2647);
        assert_eq!(m.in_pennies(), 2647);
        let m = Money::new(-95743);
        assert_eq!(m.in_pennies(), -95743);
    }

    #[test]
    fn f64_from() {
        let f = f64::from(Money::new(0));
        assert_eq!(f, 0.0);
        let f = f64::from(Money::new(43));
        assert_eq!(f, 0.43);
        let f = f64::from(Money::new(9521));
        assert_eq!(f, 95.21);
        let f = f64::from(Money::new(-7800));
        assert_eq!(f, -78.0);
        let f = f64::from(Money::new(-264789412));
        assert_eq!(f, -2647894.12);
    }

    #[test]
    fn i64_from() {
        let i = i64::from(Money::new(0));
        assert_eq!(i, 0);
        let i = i64::from(Money::new(43));
        assert_eq!(i, 0);
        let i = i64::from(Money::new(9521));
        assert_eq!(i, 95);
        let i = i64::from(Money::new(-7800));
        assert_eq!(i, -78);
        let i = i64::from(Money::new(-264789412));
        assert_eq!(i, -2647894);
    }

    #[test]
    fn bool_from() {
        assert!(!bool::from(Money::new(0)));
        assert!(bool::from(Money::new(452)));
        assert!(bool::from(Money::new(-100)));
    }

    #[test]
    fn cmp() {
        let m = Money::new(405);

        assert_eq!(m.cmp(&Money::new(398)), Ordering::Greater);
        assert_eq!(
            m.cmp(&Money::from_numeric(3.91, true).unwrap()),
            Ordering::Greater
        );
        assert_eq!(m.cmp(&Money::from(2)), Ordering::Greater);

        assert_eq!(m.cmp(&Money::new(500)), Ordering::Less);
        assert_eq!(
            m.cmp(&Money::from_numeric(4.50, true).unwrap()),
            Ordering::Less
        );
        assert_eq!(m.cmp(&Money::from(6)), Ordering::Less);

        assert_eq!(m.cmp(&Money::new(405)), Ordering::Equal);
        assert_eq!(
            m.cmp(&Money::from_numeric(4.05, true).unwrap()),
            Ordering::Equal
        );
    }

    #[test]
    fn comparisons() {
        let m1 = Money::new(-1299);
        let m2 = Money::new(-75);
        let m3 = Money::new(-75);
        let m4 = Money::new(0);
        let m5 = Money::new(512);

        assert!(m1 < m5);
        assert!(!(m1 >= m5));
        assert!(m2 < m4);
        assert!(!(m2 >= m4));

        assert!(m2 <= m3);
        assert!(!(m2 > m3));
        assert!(m1 <= m4);
        assert!(!(m1 > m4));

        assert_eq!(m2, m3);
        assert!(!(m2 != m3));
        assert_ne!(m4, m5);
        assert!(!(m4 == m5));

        assert!(m2 > m1);
        assert!(!(m2 <= m1));
        assert!(m4 > m3);
        assert!(!(m4 <= m3));

        assert!(m3 >= m2);
        assert!(!(m3 < m2));
        assert!(m5 >= m1);
        assert!(!(m5 < m1));
    }

    #[test]
    fn unary() {
        let m1 = Money::new(0);
        let m2 = Money::new(4542);
        let m3 = Money::new(-473);

        assert_eq!(-m1, Money::new(0));
        assert_eq!(-m2, Money::new(-4542));
        assert_eq!(-m3, Money::new(473));

        assert_eq!(m1.abs(), Money::new(0));
        assert_eq!(m2.abs(), Money::new(4542));
        assert_eq!(m3.abs(), Money::new(473));
    }

    #[test]
    fn add() {
        let m0 = Money::new(0);
        let m1 = Money::new(905);
        let m2 = Money::new(-63);

        assert_eq!(m0 + m1, m1);
        assert_eq!(m1 + m0, m1);
        assert_eq!(m0 + m2, m2);
        assert_eq!(m2 + m0, m2);
        assert_eq!(m1 + m2, Money::new(842));
        assert_eq!(m2 + m1, Money::new(842));

        assert_eq!(m0 + Money::from(2), Money::new(200));
        assert_eq!(m1 + Money::from(10), Money::new(1905));
        assert_eq!(m2 + Money::from(4), Money::new(337));
        assert_eq!(Money::from(61) + m0, Money::new(6100));
        assert_eq!(Money::from(8) + m1, Money::new(1705));
        assert_eq!(Money::from(40) + m2, Money::new(3937));

        assert_eq!(m0 + Money::from(-3), Money::new(-300));
        assert_eq!(m1 + Money::from(-6), Money::new(305));
        assert_eq!(m2 + Money::from(-2), Money::new(-263));
        assert_eq!(Money::from(-13) + m0, Money::new(-1300));
        assert_eq!(Money::from(-11) + m1, Money::new(-195));
        assert_eq!(Money::from(-20) + m2, Money::new(-2063));

        assert_eq!(
            m0 + Money::from_numeric(83.9, true).unwrap(),
            Money::new(8390)
        );
        assert_eq!(
            m1 + Money::from_numeric(3.06, true).unwrap(),
            Money::new(1211)
        );
        assert_eq!(
            m2 + Money::from_numeric(0.2, true).unwrap(),
            Money::new(-43)
        );
        assert_eq!(
            Money::from_numeric(6.79, true).unwrap() + m0,
            Money::new(679)
        );
        assert_eq!(
            Money::from_numeric(11., true).unwrap() + m1,
            Money::new(2005)
        );
        assert_eq!(
            Money::from_numeric(1.27, true).unwrap() + m2,
            Money::new(64)
        );

        assert_eq!(
            m0 + Money::from_numeric(-2.5, true).unwrap(),
            Money::new(-250)
        );
        assert_eq!(
            m1 + Money::from_numeric(-9.15, true).unwrap(),
            Money::new(-10)
        );
        assert_eq!(
            m2 + Money::from_numeric(-500.3, true).unwrap(),
            Money::new(-50093)
        );
        assert_eq!(
            Money::from_numeric(-1099.95, true).unwrap() + m0,
            Money::new(-109995)
        );
        assert_eq!(
            Money::from_numeric(-86.44, true).unwrap() + m1,
            Money::new(-7739)
        );
        assert_eq!(
            Money::from_numeric(-2.34, true).unwrap() + m2,
            Money::new(-297)
        );
    }

    #[test]
    fn sub() {
        let m0 = Money::new(0);
        let m1 = Money::new(1020);
        let m2 = Money::new(-4);

        assert_eq!(m0 - m1, Money::new(-1020));
        assert_eq!(m1 - m0, m1);
        assert_eq!(m0 - m2, Money::new(4));
        assert_eq!(m2 - m0, m2);
        assert_eq!(m1 - m2, Money::new(1024));
        assert_eq!(m2 - m1, Money::new(-1024));

        assert_eq!(m0 - Money::from(1), Money::new(-100));
        assert_eq!(m1 - Money::from(8), Money::new(220));
        assert_eq!(m2 - Money::from(4), Money::new(-404));
        assert_eq!(Money::from(60) - m0, Money::new(6000));
        assert_eq!(Money::from(18) - m1, Money::new(780));
        assert_eq!(Money::from(30) - m2, Money::new(3004));

        assert_eq!(m0 - Money::from(-5), Money::new(500));
        assert_eq!(m1 - Money::from(-7), Money::new(1720));
        assert_eq!(m2 - Money::from(-1), Money::new(96));
        assert_eq!(Money::from(-34) - m0, Money::new(-3400));
        assert_eq!(Money::from(-22) - m1, Money::new(-3220));
        assert_eq!(Money::from(-28) - m2, Money::new(-2796));

        assert_eq!(
            m0 - Money::from_numeric(68.04, true).unwrap(),
            Money::new(-6804)
        );
        assert_eq!(
            m1 - Money::from_numeric(3.1, true).unwrap(),
            Money::new(710)
        );
        assert_eq!(
            m2 - Money::from_numeric(0.7, true).unwrap(),
            Money::new(-74)
        );
        assert_eq!(
            Money::from_numeric(0.54, true).unwrap() - m0,
            Money::new(54)
        );
        assert_eq!(
            Money::from_numeric(14.0, true).unwrap() - m1,
            Money::new(380)
        );
        assert_eq!(
            Money::from_numeric(2.73, true).unwrap() - m2,
            Money::new(277)
        );

        assert_eq!(
            m0 - Money::from_numeric(-3.3, true).unwrap(),
            Money::new(330)
        );
        assert_eq!(
            m1 - Money::from_numeric(-98.10, true).unwrap(),
            Money::new(10830)
        );
        assert_eq!(
            m2 - Money::from_numeric(-460.8, true).unwrap(),
            Money::new(46076)
        );
        assert_eq!(
            Money::from_numeric(-4055.32, true).unwrap() - m0,
            Money::new(-405532)
        );
        assert_eq!(
            Money::from_numeric(-49.37, true).unwrap() - m1,
            Money::new(-5957)
        );
        assert_eq!(
            Money::from_numeric(-7.43, true).unwrap() - m2,
            Money::new(-739)
        );
    }

    #[test]
    fn mul() {
        let m0 = Money::new(0);
        let m1 = Money::new(25);
        let m2 = Money::new(-310);

        assert_eq!(m0 * 4, m0);
        assert_eq!(m1 * 0, m0);
        assert_eq!(m2 * 0, m0);
        assert_eq!(5 * m0, m0);
        assert_eq!(0 * m1, m0);
        assert_eq!(0 * m2, m0);

        assert_eq!(m1 * 8, Money::new(200));
        assert_eq!(m2 * 3, Money::new(-930));
        assert_eq!(m1 * -110, Money::new(-2750));
        assert_eq!(m2 * -4, Money::new(1240));
    }

    #[test]
    fn add_assign() {
        let mut m = Money::new(-100);
        m += Money::new(3);
        assert_eq!(m, Money::new(-97));
        m += Money::from(2);
        assert_eq!(m, Money::new(103));
        m += Money::from_numeric(4.56, true).unwrap();
        assert_eq!(m, Money::new(559));
        m += Money::new(-509);
        assert_eq!(m, Money::new(50));
        m += Money::from(-2);
        assert_eq!(m, Money::new(-150));
        m += Money::from_numeric(-2.54, true).unwrap();
        assert_eq!(m, Money::new(-404));
    }

    #[test]
    fn sub_assign() {
        let mut m = Money::new(200);
        m -= Money::new(40);
        assert_eq!(m, Money::new(160));
        m -= Money::from(1);
        assert_eq!(m, Money::new(60));
        m -= Money::from_numeric(2.70, true).unwrap();
        assert_eq!(m, Money::new(-210));
        m -= Money::new(-105);
        assert_eq!(m, Money::new(-105));
        m -= Money::from(-4);
        assert_eq!(m, Money::new(295));
        m -= Money::from_numeric(-1.33, true).unwrap();
        assert_eq!(m, Money::new(428));
    }

    #[test]
    fn mul_assign() {
        let mut m = Money::new(200);
        m *= 7;
        assert_eq!(m, Money::new(1400));
        m *= -3;
        assert_eq!(m, Money::new(-4200));
        m *= 2;
        assert_eq!(m, Money::new(-8400));
        m *= -10;
        assert_eq!(m, Money::new(84000));
    }

    #[test]
    fn hash() {
        let m1 = Money::new(1999);
        let m2 = Money::new(500);
        let m3 = Money::new(-3078);
        let mut hash_map = HashMap::new();

        hash_map.insert(m1, "blender");
        assert_eq!(hash_map[&m1], "blender");
        assert_eq!(
            hash_map[&Money::from_numeric(19.99, true).unwrap()],
            "blender"
        );
        hash_map.insert(m2, "five bucks");
        assert_eq!(hash_map[&m2], "five bucks");
        assert_eq!(hash_map[&Money::from(5)], "five bucks");
        assert_eq!(
            hash_map[&Money::from_numeric(5.0, true).unwrap()],
            "five bucks"
        );
        hash_map.insert(m3, "fee");
        assert_eq!(hash_map[&m3], "fee");
        assert_eq!(hash_map[&Money::from_numeric(-30.78, true).unwrap()], "fee");

        hash_map.insert(Money::from_numeric(-30.78, true).unwrap(), "refund!");
        assert_eq!(hash_map[&m3], "refund!");
        assert_eq!(
            hash_map[&Money::from_numeric(-30.78, true).unwrap()],
            "refund!"
        );

        assert!(hash_map.contains_key(&m1));
        assert!(hash_map.contains_key(&Money::from_numeric(19.99, true).unwrap()));
        assert!(hash_map.contains_key(&m2));
        assert!(hash_map.contains_key(&Money::from(5)));
        assert!(hash_map.contains_key(&Money::from_numeric(5.00, true).unwrap()));
        assert!(hash_map.contains_key(&m3));
        assert!(hash_map.contains_key(&Money::from_numeric(-30.78, true).unwrap()));

        assert!(!hash_map.contains_key(&Money::from(20)));

        hash_map.remove(&m1);
        assert!(hash_map.get(&m1).is_none());
        assert!(!hash_map.contains_key(&m1));
        assert!(hash_map
            .get(&Money::from_numeric(19.99, true).unwrap())
            .is_none());
        assert!(!hash_map.contains_key(&Money::from_numeric(19.99, true).unwrap()));

        hash_map.remove(&Money::from(5));
        assert!(hash_map.get(&m2).is_none());
        assert!(!hash_map.contains_key(&m2));
        assert!(hash_map
            .get(&Money::from_numeric(5.0, true).unwrap())
            .is_none());
        assert!(!hash_map.contains_key(&Money::from_numeric(5.0, true).unwrap()));
        assert!(hash_map.get(&Money::from(5)).is_none());
        assert!(!hash_map.contains_key(&Money::from(5)));

        hash_map.remove(&Money::from_numeric(-30.78, true).unwrap());
        assert!(hash_map.get(&m3).is_none());
        assert!(!hash_map.contains_key(&m3));
        assert!(hash_map
            .get(&Money::from_numeric(-30.78, true).unwrap())
            .is_none());
        assert!(!hash_map.contains_key(&Money::from_numeric(-30.78, true).unwrap()));

        assert_eq!(hash_map, HashMap::new());

        hash_map.insert(Money::from(10), "ten bucks");
        hash_map.insert(Money::from_numeric(50.0, true).unwrap(), "fifty bucks");
        assert_eq!(hash_map[&Money::new(1000)], "ten bucks");
        assert_eq!(hash_map[&Money::new(5000)], "fifty bucks");
    }
}
