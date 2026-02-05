use std::error::Error;
use std::fmt::{self, Display};
use std::num::ParseIntError;

use lazy_static;
use regex::Regex;

lazy_static::lazy_static! {
    // This regex lays out the *proper* format of a comma-separated integer
    static ref COMMA_INT_FORMAT: Regex = Regex::new(r"(?x)
        \A\s*            # Optional leading whitespace
        (?P<sign>[-+]?)  # Possible sign character
        (?P<body>        # The body of the integer is either
            \d+          # an uninterrupted string of one or more digits
        |                # or
            \d{1,3}      # a string of one to three digits followed by
            (?:,\d{3})+  # one or more comma-separated triples of digits
        )
        \s*\z            # Optional trailing whitespace
    ").expect("COMMA_INT_FORMAT regex should compile without issues");
}

#[derive(Debug, PartialEq)]
pub enum CommaIntError {
    FormatFailure(String),
    LeadingZero,
    ParseError(ParseIntError),
}

impl Display for CommaIntError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::FormatFailure(string) => {
                write!(f, "incorrect format for comma-separated int: {:?}", string)
            }
            Self::LeadingZero => {
                write!(f, "leading zero illegal in comma-separated int")
            }
            Self::ParseError(error) => {
                write!(f, "{}", error)
            }
        }
    }
}

impl Error for CommaIntError {}

/// Parse an integer value from a string that may include commas.
///
/// The string may optionally include commas if used correctly as digit
/// separators. For example, the input "23,009,108" produces the int 23009108.
/// If commas *are* included in the string, then their usage *must* be correct,
/// meaning that they must delimit *every* set of three digits starting from
/// the rightmost. Incorrect placement signals a possible typo, and this
/// function will therefore return the Err variant. The use of leading zeros
/// will also raise an exception unless the leading zero is the only digit
/// present, i.e., the input represents the integer 0 itself.
pub fn parse_comma_int(string: &str) -> Result<i64, CommaIntError> {
    let captures = match COMMA_INT_FORMAT.captures(string) {
        Some(captures) => captures,
        None => return Err(CommaIntError::FormatFailure(string.to_owned())),
    };

    let body = captures
        .name("body")
        .expect("named group 'body' should be valid if regex matches")
        .as_str();
    let body_without_commas = body.replace(",", "");
    if body_without_commas != "0" && body_without_commas.starts_with('0') {
        return Err(CommaIntError::LeadingZero);
    }

    let integer_abs: i64 = match body_without_commas.parse() {
        Ok(integer_abs) => integer_abs,
        Err(error) => return Err(CommaIntError::ParseError(error)),
    };

    let sign = captures
        .name("sign")
        .expect("named group 'sign' should be valid if regex matches")
        .as_str();
    Ok(if sign == "-" {
        -integer_abs
    } else {
        integer_abs
    })
}

/// Render an integer value to a string with commas inserted as needed.
///
/// Zero or more commas will be inserted as digit separators every set of three
/// digits from the right. For example, an input value of 23009108 produces the
/// string "23,009,108". This is intended as a pretty-printing function for
/// improved readability of large integers, but also demonstrates the correct
/// input format required by the parse_comma_int() function.
pub fn render_comma_int(integer: i64) -> String {
    // Numbers with fewer than three digits don't need commas
    if integer.abs() < 1_000 {
        return integer.to_string();
    }

    let sign = if integer < 0 { "-" } else { "" };
    let mut unsigned = integer.abs() as u64;

    // Build up the final string backwards, one char at a time. Whenever we go
    // to add another digit and the number of existing digits is a positive
    // multiple of 3, insert a comma first.
    let mut backwards = String::new();
    let mut n_digits: usize = 0;
    while unsigned > 0 {
        let (q, r) = (unsigned / 10, unsigned % 10);
        let digit = (('0' as u8) + (r as u8)) as char;
        if n_digits > 0 && n_digits % 3 == 0 {
            backwards.push(',');
        }
        backwards.push(digit);
        n_digits += 1;
        unsigned = q;
    }

    backwards.push_str(sign);
    backwards.chars().rev().collect()
}

#[cfg(test)]
mod test_comma_int {
    use super::*;

    #[test]
    fn parse_comma_int_happy() {
        assert_eq!(parse_comma_int("0"), Ok(0));
        assert_eq!(parse_comma_int("-0"), Ok(0));
        assert_eq!(parse_comma_int("+0"), Ok(0));

        assert_eq!(parse_comma_int("8"), Ok(8));
        assert_eq!(parse_comma_int("-2"), Ok(-2));
        assert_eq!(parse_comma_int("+3"), Ok(3));

        assert_eq!(parse_comma_int("45"), Ok(45));
        assert_eq!(parse_comma_int("-90"), Ok(-90));
        assert_eq!(parse_comma_int("+97"), Ok(97));

        assert_eq!(parse_comma_int("761"), Ok(761));
        assert_eq!(parse_comma_int("-388"), Ok(-388));
        assert_eq!(parse_comma_int("+74"), Ok(74));

        assert_eq!(parse_comma_int("1,024"), Ok(1024));
        assert_eq!(parse_comma_int("2048"), Ok(2048));
        assert_eq!(parse_comma_int("-3,355"), Ok(-3355));
        assert_eq!(parse_comma_int("-5533"), Ok(-5533));
        assert_eq!(parse_comma_int("+5,289"), Ok(5289));
        assert_eq!(parse_comma_int("+1243"), Ok(1243));

        assert_eq!(parse_comma_int("65,388"), Ok(65388));
        assert_eq!(parse_comma_int("54321"), Ok(54321));
        assert_eq!(parse_comma_int("-25,126"), Ok(-25126));
        assert_eq!(parse_comma_int("-36548"), Ok(-36548));
        assert_eq!(parse_comma_int("+25,289"), Ok(25289));
        assert_eq!(parse_comma_int("+12643"), Ok(12643));

        assert_eq!(parse_comma_int("333,444"), Ok(333444));
        assert_eq!(parse_comma_int("556677"), Ok(556677));
        assert_eq!(parse_comma_int("-730,123"), Ok(-730123));
        assert_eq!(parse_comma_int("-267922"), Ok(-267922));
        assert_eq!(parse_comma_int("+528,669"), Ok(528669));
        assert_eq!(parse_comma_int("+812843"), Ok(812843));

        assert_eq!(parse_comma_int("1,000,456"), Ok(1000456));
        assert_eq!(parse_comma_int("9753197"), Ok(9753197));
        assert_eq!(parse_comma_int("-3,644,895"), Ok(-3644895));
        assert_eq!(parse_comma_int("-3225699"), Ok(-3225699));
        assert_eq!(parse_comma_int("+5,289,156"), Ok(5289156));
        assert_eq!(parse_comma_int("+1243637"), Ok(1243637));

        assert_eq!(parse_comma_int("23,009,108"), Ok(23009108));
        assert_eq!(parse_comma_int("44556778"), Ok(44556778));
        assert_eq!(parse_comma_int("-66,559,874"), Ok(-66559874));
        assert_eq!(parse_comma_int("-15478888"), Ok(-15478888));
        assert_eq!(parse_comma_int("+35,289,156"), Ok(35289156));
        assert_eq!(parse_comma_int("+71243637"), Ok(71243637));

        assert_eq!(parse_comma_int("23,009,108"), Ok(23009108));
        assert_eq!(parse_comma_int("44556778"), Ok(44556778));
        assert_eq!(parse_comma_int("-232,545,968"), Ok(-232545968));
        assert_eq!(parse_comma_int("-165489512"), Ok(-165489512));
        assert_eq!(parse_comma_int("+365,289,156"), Ok(365289156));
        assert_eq!(parse_comma_int("+701243637"), Ok(701243637));
    }

    #[test]
    fn parse_comma_int_pedantry() {
        assert!(parse_comma_int("").is_err());
        assert!(parse_comma_int("1,2").is_err());
        assert!(parse_comma_int(",").is_err());
        assert!(parse_comma_int("02,456").is_err());
        assert!(parse_comma_int("00").is_err());
    }

    #[test]
    fn render_comma_int_happy() {
        assert_eq!(render_comma_int(0), "0");

        assert_eq!(render_comma_int(4), "4");
        assert_eq!(render_comma_int(-8), "-8");
        assert_eq!(render_comma_int(66), "66");
        assert_eq!(render_comma_int(-31), "-31");
        assert_eq!(render_comma_int(458), "458");
        assert_eq!(render_comma_int(-900), "-900");

        assert_eq!(render_comma_int(4096), "4,096");
        assert_eq!(render_comma_int(-2654), "-2,654");
        assert_eq!(render_comma_int(33256), "33,256");
        assert_eq!(render_comma_int(-32554), "-32,554");
        assert_eq!(render_comma_int(445988), "445,988");
        assert_eq!(render_comma_int(-998775), "-998,775");

        assert_eq!(render_comma_int(5455977), "5,455,977");
        assert_eq!(render_comma_int(-1324266), "-1,324,266");
        assert_eq!(render_comma_int(23009108), "23,009,108");
        assert_eq!(render_comma_int(-87532786), "-87,532,786");
        assert_eq!(render_comma_int(978498349), "978,498,349");
        assert_eq!(render_comma_int(-548937984), "-548,937,984");
    }

    #[test]
    fn comma_int_round_trips() {
        let integers = [
            0, 5, -6, 10, -14, 869, -364, 8497, -4890, 74784, -98909, 484655, -656456, 2256638,
            -1569348, 16666587, -97889753, 978897528, -477292004,
        ];
        for i in integers {
            let s = render_comma_int(i);
            let i2 = parse_comma_int(&s).unwrap();
            assert_eq!(i2, i);
            let s2 = render_comma_int(i2);
            assert_eq!(s2, s);
        }
    }
}
