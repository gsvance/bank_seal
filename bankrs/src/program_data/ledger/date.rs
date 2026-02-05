use std::collections::HashMap;
use std::error::Error;
use std::fmt::{self, Display};
use std::num::ParseIntError;
use std::str::FromStr;

use chrono::{self, Datelike};
use lazy_static;
use regex::Regex;
use serde::{Deserialize, Serialize};

const YEAR_MIN: u16 = 1980; // Earliest acceptable year (for sanity checks)
const YEAR_MAX: u16 = 2100; // Latest acceptable year (also for sanity checks)

const MONTH_MIN: u8 = 1;
const MONTH_MAX: u8 = 12;
const MONTH_COUNT: u8 = MONTH_MAX - MONTH_MIN + 1;

lazy_static::lazy_static! {
    static ref MONTH_NAMES: HashMap<u8, &'static str> = {
        let mut names = HashMap::new();
        names.insert(1, "Jan");
        names.insert(2, "Feb");
        names.insert(3, "Mar");
        names.insert(4, "Apr");
        names.insert(5, "May");
        names.insert(6, "Jun");
        names.insert(7, "Jul");
        names.insert(8, "Aug");
        names.insert(9, "Sep");
        names.insert(10, "Oct");
        names.insert(11, "Nov");
        names.insert(12, "Dec");
        names
    };
}

lazy_static::lazy_static! {
    static ref MONTH_NUMBERS: HashMap<&'static str, u8> = {
        let mut numbers = HashMap::new();
        for (number, name) in MONTH_NAMES.iter() {
            numbers.insert(name as &'static str, *number);
        }
        numbers
    };
}

const DAY_MIN: u8 = 1;

lazy_static::lazy_static! {
    static ref MONTH_DAYS: HashMap<u8, u8> = {
        let mut days = HashMap::new();
        days.insert(1, 31);
        days.insert(2, 28);
        days.insert(3, 31);
        days.insert(4, 30);
        days.insert(5, 31);
        days.insert(6, 30);
        days.insert(7, 31);
        days.insert(8, 31);
        days.insert(9, 30);
        days.insert(10, 31);
        days.insert(11, 30);
        days.insert(12, 31);
        days
    };
}

const LEAP_DAY_MONTH: u8 = 2; // February is the leap day month

lazy_static::lazy_static! {
    // Match dates using the traditional American format "m/d/y"
    static ref DATE_FORMAT_USA: Regex = regex::Regex::new(r"(?x)
        \A\s*           # Optional leading whitespace
        (?P<month>      # The month comes first and consists of
            \d{1,2}     # either one or two digits
        )
        /               # Month and day are separated by '/'
        (?P<day>        # The day comes second and also consists of
            \d{1,2}     # either one or two digits
        )
        (?: /           # Day and year are separated by '/'
        (?P<year>       # The year comes last and consists of
            \d{2}|\d{4} # either two or four digits
        ) )?            # The whole /year bit is actually optional
        \s*\z           # Optional trailing whitespace
    ").expect("DATE_FORMAT_USA regex should compile without issues");

    // Match dates using the more international format "d mmm y"
    static ref DATE_FORMAT_INTL: Regex = Regex::new(r"(?x)
        \A\s*              # Optional leading whitespace
        (?P<day>           # First comes the day, which consists of
            \d{1,2}        # either one or two digits
        )
        \ +                # One or more space characters between day and month
        (?P<month>         # Second is the month, which is written as
            [A-Z][a-z]{2}  # a title-case sequence of three letters
        )
        (?: \ +            # One or more space characters between month and year
        (?P<year>          # Last is the year, which can be
            \d{2}|\d{4}    # either two or four digits
        ) )?               # The whole spaces + year bit is actually optional
        \s*\z              # Optional trailing whitespace
    ").expect("DATE_FORMAT_INTL regex should compile without issues");
}

#[derive(Debug, PartialEq)]
pub enum DateError {
    BadYearHint(u16),
    BadMonthName(String),
    IntParseError(ParseIntError),
    FormatFailure(String),
    BeforeYearMin(u16),
    AfterYearMax(u16),
    IllegalMonth(u8),
    IllegalDay(u8),
    AfterMonthEnd { day: u8, month: u8, year: u16 },
}

impl Display for DateError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::BadYearHint(hint) => write!(f, "year hint {} could not be interpreted", hint),
            Self::BadMonthName(name) => write!(f, "unknown month name: {:?}", name),
            Self::IntParseError(error) => write!(f, "{}", error),
            Self::FormatFailure(string) => write!(f, "incorrect format for date: {:?}", string),
            Self::BeforeYearMin(year) => {
                write!(f, "year {} is before minimum year ({})", year, YEAR_MIN)
            }
            Self::AfterYearMax(year) => {
                write!(f, "year {} is after maximum year ({})", year, YEAR_MAX)
            }
            Self::IllegalMonth(month) => write!(
                f,
                "month {} is illegal, must range from {} to {}",
                month, MONTH_MIN, MONTH_MAX
            ),
            Self::IllegalDay(day) => {
                write!(f, "day {} is illegal, must be at least {}", day, DAY_MIN)
            }
            Self::AfterMonthEnd { day, month, year } => write!(
                f,
                "day {} is after end of month ({} {})",
                day, MONTH_NAMES[month], year
            ),
        }
    }
}

impl Error for DateError {}

#[derive(Debug, Clone, Copy, PartialOrd, Ord, PartialEq, Eq, Hash, Deserialize, Serialize)]
pub struct Date {
    year: u16,
    month: u8,
    day: u8,
}

impl Date {
    pub fn new(year: u16, month: u8, day: u8) -> Result<Self, DateError> {
        let date = Self { year, month, day };
        date.validate()
    }

    pub fn today() -> Self {
        let chrono_date = chrono::Local::now().date_naive();

        let current_year: u16 = chrono_date
            .year()
            .try_into()
            .expect("current year should fit into a u16");
        let current_month0: u8 = chrono_date
            .month0()
            .try_into()
            .expect("current zero-based month should fit into a u8");
        let current_day0: u8 = chrono_date
            .day0()
            .try_into()
            .expect("current zero-based day should fit into a u8");

        Self::new(
            current_year,
            current_month0 + MONTH_MIN,
            current_day0 + DAY_MIN,
        )
        .expect("current date should be valid until year = YEAR_MAX")
    }
}

impl Date {
    fn infer_year(year_hint: Option<u16>, month: u8, day: u8) -> Result<Self, DateError> {
        match year_hint {
            Some(hint) if (1000..=9999).contains(&hint) => {
                let four_digit_year = hint;
                Date::new(four_digit_year, month, day)
            }

            Some(hint) if (0..=99).contains(&hint) => {
                let two_digit_year = hint;
                let current_year = Date::today().year;
                let current_century = (current_year / 100) * 100;
                let century_options = [
                    current_century,
                    current_century - 100,
                    current_century + 100,
                ];
                let inferred_century = century_options
                    .into_iter()
                    .min_by_key(|&century| (century + two_digit_year).abs_diff(current_year))
                    .expect("array of 3 elements should have a minimum");
                Date::new(inferred_century + two_digit_year, month, day)
            }

            None => {
                let today = Date::today();
                let (current_year, current_month) = (today.year, today.month);
                let year_options = [current_year, current_year - 1, current_year + 1];
                let inferred_year = year_options
                    .into_iter()
                    .min_by_key(|&year| {
                        let year_months =
                            year as u32 * MONTH_COUNT as u32 + month as u32 - MONTH_MIN as u32;
                        let curr_months = current_year as u32 * MONTH_COUNT as u32
                            + current_month as u32
                            - MONTH_MIN as u32;
                        year_months.abs_diff(curr_months)
                    })
                    .expect("array of 3 elements should have a minimum");
                Date::new(inferred_year, month, day)
            }

            Some(bad_hint) => Err(DateError::BadYearHint(bad_hint)),
        }
    }
}

impl FromStr for Date {
    type Err = DateError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Some(captures) = DATE_FORMAT_USA.captures(s) {
            let month = captures
                .name("month")
                .expect("named group 'month' should be valid if regex matches")
                .as_str();
            let month = match month.parse() {
                Ok(integer) => integer,
                Err(error) => return Err(DateError::IntParseError(error)),
            };
            let day = captures
                .name("day")
                .expect("named group 'day' should be valid if regex matches")
                .as_str();
            let day = match day.parse() {
                Ok(integer) => integer,
                Err(error) => return Err(DateError::IntParseError(error)),
            };
            let year_hint = captures.name("year").map(|y| y.as_str());
            let year_hint = match year_hint.map(|y| y.parse()) {
                Some(Ok(integer)) => Some(integer),
                Some(Err(error)) => return Err(DateError::IntParseError(error)),
                None => None,
            };
            return Date::infer_year(year_hint, month, day);
        }

        if let Some(captures) = DATE_FORMAT_INTL.captures(s) {
            let day = captures
                .name("day")
                .expect("named group 'day' should be valid if regex matches")
                .as_str();
            let day = match day.parse() {
                Ok(integer) => integer,
                Err(error) => return Err(DateError::IntParseError(error)),
            };
            let month = captures
                .name("month")
                .expect("named group 'month' should be valid if regex matches")
                .as_str();
            let month = match MONTH_NUMBERS.get(month) {
                Some(integer) => *integer,
                None => return Err(DateError::BadMonthName(month.to_owned())),
            };
            let year_hint = captures.name("year").map(|y| y.as_str());
            let year_hint = match year_hint.map(|y| y.parse()) {
                Some(Ok(integer)) => Some(integer),
                Some(Err(error)) => return Err(DateError::IntParseError(error)),
                None => None,
            };
            return Date::infer_year(year_hint, month, day);
        }

        Err(DateError::FormatFailure(s.to_owned()))
    }
}

impl Display for Date {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} {} {}", self.day, self.month_name(), self.year)
    }
}

impl Date {
    fn validate(self) -> Result<Self, DateError> {
        if self.year < YEAR_MIN {
            Err(DateError::BeforeYearMin(self.year))
        } else if self.year > YEAR_MAX {
            Err(DateError::AfterYearMax(self.year))
        } else if self.month < MONTH_MIN || self.month > MONTH_MAX {
            Err(DateError::IllegalMonth(self.month))
        } else if self.day < DAY_MIN {
            Err(DateError::IllegalDay(self.day))
        } else if self.day > self.month_length() {
            Err(DateError::AfterMonthEnd {
                day: self.day,
                month: self.month,
                year: self.year,
            })
        } else {
            Ok(self)
        }
    }
}

impl Date {
    fn month_name(&self) -> &'static str {
        MONTH_NAMES[&self.month]
    }

    fn month_length(&self) -> u8 {
        let days = MONTH_DAYS[&self.month];
        if self.month == LEAP_DAY_MONTH && self.in_leap_year() {
            days + 1
        } else {
            days
        }
    }

    fn in_leap_year(self) -> bool {
        let multiple_of_4 = self.year % 4 == 0;
        let not_a_century = self.year % 100 != 0;
        let multiple_of_400 = self.year % 400 == 0;
        multiple_of_4 && (not_a_century || multiple_of_400)
    }
}

impl Date {
    pub fn year(&self) -> u16 {
        self.year
    }

    pub fn month(&self) -> u8 {
        self.month
    }

    pub fn day(&self) -> u8 {
        self.day
    }
}

#[cfg(test)]
mod test_date {
    use super::*;

    #[test]
    fn new() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(d.year, 2023);
        assert_eq!(d.month, 2);
        assert_eq!(d.day, 6);
        let d = Date::new(1993, 4, 11).unwrap();
        assert_eq!(d.year, 1993);
        assert_eq!(d.month, 4);
        assert_eq!(d.day, 11);
        let d = Date::new(2016, 2, 29).unwrap();
        assert_eq!(d.year, 2016);
        assert_eq!(d.month, 2);
        assert_eq!(d.day, 29);
        let d = Date::new(1995, 10, 16).unwrap();
        assert_eq!(d.year, 1995);
        assert_eq!(d.month, 10);
        assert_eq!(d.day, 16);
    }

    #[test]
    fn today() {
        let d = Date::today();
        let chrono_today = chrono::Local::now().date_naive();
        assert_eq!(d.year as i64, chrono_today.year() as i64);
        assert_eq!(d.month as i64, chrono_today.month0() as i64 + 1);
        assert_eq!(d.day as i64, chrono_today.day0() as i64 + 1);
    }

    #[test]
    fn infer_year() {
        let current_year = chrono::Local::now().date_naive().year() as u16;
        for year in (current_year - 30)..=(current_year + 30) {
            let two_digit = year % 100;
            let d4 = Date::infer_year(Some(year), 5, 20).unwrap();
            assert_eq!(d4.year, year);
            assert_eq!(d4.month, 5);
            assert_eq!(d4.day, 20);
            let d2 = Date::infer_year(Some(two_digit), 5, 20).unwrap();
            assert_eq!(d2.year, year);
            assert_eq!(d2.month, 5);
            assert_eq!(d2.day, 20);
        }

        let current_month = chrono::Local::now().date_naive().month0() as u8 + 1;
        for unbounded_month in (current_month as i8 - 5)..=(current_month as i8 + 5) {
            let month;
            let year;
            if unbounded_month < 1 {
                month = (unbounded_month + 12) as u8;
                year = current_year - 1;
            } else if unbounded_month > 12 {
                month = (unbounded_month - 12) as u8;
                year = current_year + 1;
            } else {
                month = unbounded_month as u8;
                year = current_year;
            }
            let d = Date::infer_year(None, month, 10).unwrap();
            assert_eq!(d.year, year);
            assert_eq!(d.month, month);
            assert_eq!(d.day, 10);
        }

        assert!(Date::infer_year(Some(321), 4, 10).is_err());
        assert!(Date::infer_year(Some(54321), 4, 10).is_err());
        assert!(Date::infer_year(Some(100), 4, 10).is_err());
    }

    #[test]
    fn parse_succeeds() {
        let current_year = chrono::Local::now().date_naive().year() as u16;

        let d: Date = "12/22/2023".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "12/22/23".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "1/22/2023".parse().unwrap();
        assert_eq!(d.month, 1);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "1/22/23".parse().unwrap();
        assert_eq!(d.month, 1);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "12/6/2023".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 6);
        assert_eq!(d.year, 2023);

        let d: Date = "12/6/23".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 6);
        assert_eq!(d.year, 2023);

        let d: Date = "6/30".parse().unwrap();
        assert_eq!(d.month, 6);
        assert_eq!(d.day, 30);
        assert_eq!(d.year, current_year);

        let d: Date = "7/1".parse().unwrap();
        assert_eq!(d.month, 7);
        assert_eq!(d.day, 1);
        assert_eq!(d.year, current_year);

        let d: Date = "22 Dec 2023".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "22 Dec 23".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "22 Jan 2023".parse().unwrap();
        assert_eq!(d.month, 1);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "22 Jan 23".parse().unwrap();
        assert_eq!(d.month, 1);
        assert_eq!(d.day, 22);
        assert_eq!(d.year, 2023);

        let d: Date = "6 Dec 2023".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 6);
        assert_eq!(d.year, 2023);

        let d: Date = "6 Dec 23".parse().unwrap();
        assert_eq!(d.month, 12);
        assert_eq!(d.day, 6);
        assert_eq!(d.year, 2023);

        let d: Date = "30 Jun".parse().unwrap();
        assert_eq!(d.month, 6);
        assert_eq!(d.day, 30);
        assert_eq!(d.year, current_year);

        let d: Date = "1 Jul".parse().unwrap();
        assert_eq!(d.month, 7);
        assert_eq!(d.day, 1);
        assert_eq!(d.year, current_year);
    }

    #[test]
    fn parse_fails() {
        let garbage = [
            "",
            "/",
            "//",
            "May",
            "13",
            "2012",
            " ",
            "11//2020",
            "/5/1999",
            "10/2/",
            "123/4/2007",
            "9/321/2009",
            "7/21/54321",
            "6/30/543",
            " Feb 21",
            "21  2011",
            "3 Mar 123",
            "4 Mar 54321",
            "234 Apr 2000",
            "5 Grb 2004",
            "12 Bla 97",
        ];
        for snotty_tissue in garbage {
            assert!(snotty_tissue.parse::<Date>().is_err());
        }
    }

    #[test]
    fn display() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(d.to_string(), "6 Feb 2023");
        let d = Date::new(2002, 12, 25).unwrap();
        assert_eq!(d.to_string(), "25 Dec 2002");
        let d = Date::new(2011, 9, 30).unwrap();
        assert_eq!(d.to_string(), "30 Sep 2011");
        let d = Date::new(2018, 3, 10).unwrap();
        assert_eq!(d.to_string(), "10 Mar 2018");
    }

    #[test]
    fn debug() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(format!("{:?}", d), "Date { year: 2023, month: 2, day: 6 }");
        let d = Date::new(2005, 8, 1).unwrap();
        assert_eq!(format!("{:?}", d), "Date { year: 2005, month: 8, day: 1 }");
        let d = Date::new(1999, 11, 11).unwrap();
        assert_eq!(
            format!("{:?}", d),
            "Date { year: 1999, month: 11, day: 11 }"
        );
        let d = Date::new(2015, 5, 20).unwrap();
        assert_eq!(format!("{:?}", d), "Date { year: 2015, month: 5, day: 20 }");
    }

    #[test]
    fn validate() {
        assert_eq!(Date::new(1840, 5, 10), Err(DateError::BeforeYearMin(1840)));
        assert_eq!(Date::new(2300, 1, 31), Err(DateError::AfterYearMax(2300)));
        assert_eq!(Date::new(2013, 0, 12), Err(DateError::IllegalMonth(0)));
        assert_eq!(Date::new(2013, 14, 27), Err(DateError::IllegalMonth(14)));
        assert_eq!(Date::new(2013, 7, 0), Err(DateError::IllegalDay(0)));
        assert_eq!(
            Date::new(2013, 4, 31),
            Err(DateError::AfterMonthEnd {
                day: 31,
                month: 4,
                year: 2013
            })
        );
        assert_eq!(
            Date::new(2021, 2, 29),
            Err(DateError::AfterMonthEnd {
                day: 29,
                month: 2,
                year: 2021
            })
        );
    }

    #[test]
    fn month_name() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(d.month_name(), "Feb");
        let d = Date::new(2008, 4, 12).unwrap();
        assert_eq!(d.month_name(), "Apr");
        let d = Date::new(2015, 10, 24).unwrap();
        assert_eq!(d.month_name(), "Oct");
        let d = Date::new(2020, 7, 17).unwrap();
        assert_eq!(d.month_name(), "Jul");
        let d = Date::new(1996, 8, 2).unwrap();
        assert_eq!(d.month_name(), "Aug");
    }

    #[test]
    fn month_length() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(d.month_length(), 28);
        let d = Date::new(2024, 2, 18).unwrap();
        assert_eq!(d.month_length(), 29);
        let d = Date::new(2012, 1, 29).unwrap();
        assert_eq!(d.month_length(), 31);
        let d = Date::new(1994, 4, 11).unwrap();
        assert_eq!(d.month_length(), 30);
        let d = Date::new(1999, 8, 11).unwrap();
        assert_eq!(d.month_length(), 31);
    }

    #[test]
    fn in_leap_year() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert!(!d.in_leap_year());
        let d = Date::new(2024, 3, 17).unwrap();
        assert!(d.in_leap_year());
        let d = Date::new(2004, 9, 3).unwrap();
        assert!(d.in_leap_year());
        let d = Date::new(2000, 5, 9).unwrap();
        assert!(d.in_leap_year());
        let d = Date::new(1999, 6, 11).unwrap();
        assert!(!d.in_leap_year());
    }

    #[test]
    fn year_month_day() {
        let d = Date::new(2023, 2, 6).unwrap();
        assert_eq!(d.year(), 2023);
        assert_eq!(d.month(), 2);
        assert_eq!(d.day(), 6);
        let d = Date::new(1995, 6, 22).unwrap();
        assert_eq!(d.year(), 1995);
        assert_eq!(d.month(), 6);
        assert_eq!(d.day(), 22);
    }

    #[test]
    fn comparisons() {
        let d1 = Date::new(1993, 4, 11).unwrap();
        let d2 = Date::new(1995, 10, 16).unwrap();
        let d3 = Date::new(1995, 10, 16).unwrap();
        let d4 = Date::new(2015, 4, 25).unwrap();
        let d5 = Date::new(2015, 5, 20).unwrap();
        let d6 = Date::new(2023, 5, 30).unwrap();

        assert!(d1 < d5);
        assert!(!(d1 >= d5));
        assert!(d3 < d4);
        assert!(!(d3 >= d4));

        assert!(d2 <= d3);
        assert!(!(d2 > d3));
        assert!(d2 <= d6);
        assert!(!(d2 > d6));

        assert_eq!(d2, d3);
        assert!(!(d2 != d3));
        assert_ne!(d3, d4);
        assert!(!(d3 == d4));

        assert!(d5 > d4);
        assert!(!(d5 <= d4));
        assert!(d6 > d1);
        assert!(!(d6 <= d1));

        assert!(d2 >= d3);
        assert!(!(d2 < d3));
        assert!(d5 >= d4);
        assert!(!(d5 < d4));
    }

    #[test]
    fn hash() {
        let d1 = Date::new(2023, 2, 6).unwrap();
        let d2 = Date::new(1995, 10, 16).unwrap();
        let d3 = Date::new(2021, 11, 3).unwrap();
        let mut hash_map = HashMap::new();

        hash_map.insert(d1, "unit tests");
        assert_eq!(hash_map[&d1], "unit tests");
        hash_map.insert(d2, "jimothy");
        assert_eq!(hash_map[&d2], "jimothy");
        hash_map.insert(d3, "narrows");
        assert_eq!(hash_map[&d3], "narrows");

        hash_map.insert(d3, "success!");
        assert_eq!(hash_map[&d3], "success!");

        hash_map.remove(&d1);
        assert!(hash_map.get(&d1).is_none());

        assert!(hash_map.contains_key(&d2));
        assert!(!hash_map.contains_key(&d1));
    }
}
