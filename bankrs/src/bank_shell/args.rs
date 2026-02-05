use std::collections::VecDeque;
use std::error::Error;
use std::fmt::{self, Display};

use crate::program_data::{Date, Money};

#[derive(Debug, PartialEq)]
pub enum SplitError {
    SpacingMissing,
    UnclosedQuotes,
    EscapedNewline,
}

impl Display for SplitError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SpacingMissing => write!(f, "shell arguments must be separated by whitespace"),
            Self::UnclosedQuotes => write!(f, "input line ended while parsing quoted argument"),
            Self::EscapedNewline => write!(f, "input line cannot end with escape character"),
        }
    }
}

impl Error for SplitError {}

enum SplitState<'a> {
    BetweenArgs { seen_space: bool },
    InUnquotedArg { arg: &'a mut String, escaped: bool },
    InSingleQuotedArg { arg: &'a mut String, escaped: bool },
    InDoubleQuotedArg { arg: &'a mut String, escaped: bool },
}

const SINGLE_QUOTE: char = '\'';
const DOUBLE_QUOTE: char = '"';
const BACKSLASH: char = '\\';

pub fn split(line: &str) -> Result<VecDeque<String>, SplitError> {
    let mut args = VecDeque::new();
    let mut state = SplitState::BetweenArgs {
        seen_space: true, // Ready to parse first arg immediately
    };

    for character in line.chars() {
        match &mut state {
            SplitState::BetweenArgs { seen_space } => {
                if character.is_whitespace() {
                    *seen_space = true;
                    continue;
                } else if !(*seen_space) {
                    return Err(SplitError::SpacingMissing);
                }
                args.push_back(String::new());
                let new_arg = args.back_mut().expect("newly pushed string exists");
                state = match character {
                    SINGLE_QUOTE => SplitState::InSingleQuotedArg {
                        arg: new_arg,
                        escaped: false,
                    },
                    DOUBLE_QUOTE => SplitState::InDoubleQuotedArg {
                        arg: new_arg,
                        escaped: false,
                    },
                    BACKSLASH => SplitState::InUnquotedArg {
                        arg: new_arg,
                        escaped: true,
                    },
                    _ => {
                        new_arg.push(character);
                        SplitState::InUnquotedArg {
                            arg: new_arg,
                            escaped: false,
                        }
                    }
                }
            }

            SplitState::InUnquotedArg { arg, escaped } => {
                if *escaped {
                    arg.push(character);
                    *escaped = false;
                } else if character == BACKSLASH {
                    *escaped = true;
                } else if character.is_whitespace() {
                    state = SplitState::BetweenArgs { seen_space: true };
                } else {
                    arg.push(character);
                }
            }

            SplitState::InSingleQuotedArg { arg, escaped } => {
                if *escaped {
                    arg.push(character);
                    *escaped = false;
                } else if character == BACKSLASH {
                    *escaped = true;
                } else if character == SINGLE_QUOTE {
                    state = SplitState::BetweenArgs { seen_space: false };
                } else {
                    arg.push(character);
                }
            }

            SplitState::InDoubleQuotedArg { arg, escaped } => {
                if *escaped {
                    arg.push(character);
                    *escaped = false;
                } else if character == BACKSLASH {
                    *escaped = true;
                } else if character == DOUBLE_QUOTE {
                    state = SplitState::BetweenArgs { seen_space: false };
                } else {
                    arg.push(character);
                }
            }
        }
    }

    match state {
        SplitState::InSingleQuotedArg { .. } => Err(SplitError::UnclosedQuotes),
        SplitState::InDoubleQuotedArg { .. } => Err(SplitError::UnclosedQuotes),
        SplitState::InUnquotedArg { escaped: true, .. } => Err(SplitError::EscapedNewline),
        _ => Ok(args),
    }
}

#[cfg(test)]
mod test_split {
    use super::*;

    #[test]
    fn whitespace() {
        let line1 = "basic arg split";
        let answer1 = VecDeque::from([
            String::from("basic"),
            String::from("arg"),
            String::from("split"),
        ]);
        let line2 = " example\t for whitespace   test  ";
        let answer2 = VecDeque::from([
            String::from("example"),
            String::from("for"),
            String::from("whitespace"),
            String::from("test"),
        ]);
        let line3 = "";
        let answer3 = VecDeque::new();

        let result1 = split(line1);
        let result2 = split(line2);
        let result3 = split(line3);

        assert_eq!(result1, Ok(answer1));
        assert_eq!(result2, Ok(answer2));
        assert_eq!(result3, Ok(answer3));
    }

    #[test]
    fn single_quoted() {
        let line1 = "'quoted' 'example' for 'split test'";
        let answer1 = VecDeque::from([
            String::from("quoted"),
            String::from("example"),
            String::from("for"),
            String::from("split test"),
        ]);
        let line2 = "another 'example for ' '' ' testing'";
        let answer2 = VecDeque::from([
            String::from("another"),
            String::from("example for "),
            String::from(""),
            String::from(" testing"),
        ]);
        let line3 = "this '\"supposedly\"' works";
        let answer3 = VecDeque::from([
            String::from("this"),
            String::from("\"supposedly\""),
            String::from("works"),
        ]);

        let result1 = split(line1);
        let result2 = split(line2);
        let result3 = split(line3);

        assert_eq!(result1, Ok(answer1));
        assert_eq!(result2, Ok(answer2));
        assert_eq!(result3, Ok(answer3));
    }

    #[test]
    fn double_quoted() {
        let line1 = "\"quoted\" \"example\" for \"split test\"";
        let answer1 = VecDeque::from([
            String::from("quoted"),
            String::from("example"),
            String::from("for"),
            String::from("split test"),
        ]);
        let line2 = "another \"example for \" \"\" \" testing\"";
        let answer2 = VecDeque::from([
            String::from("another"),
            String::from("example for "),
            String::from(""),
            String::from(" testing"),
        ]);
        let line3 = "these \"shouldn't\" misbehave";
        let answer3 = VecDeque::from([
            String::from("these"),
            String::from("shouldn't"),
            String::from("misbehave"),
        ]);

        let result1 = split(line1);
        let result2 = split(line2);
        let result3 = split(line3);

        assert_eq!(result1, Ok(answer1));
        assert_eq!(result2, Ok(answer2));
        assert_eq!(result3, Ok(answer3));
    }

    #[test]
    fn escapes() {
        let line1 = "\\  \\ \\  couldn\\'t spa\\ ce";
        let answer1 = VecDeque::from([
            String::from(" "),
            String::from("  "),
            String::from("couldn't"),
            String::from("spa ce"),
        ]);
        let line2 = "abc\\\"de \\\\  ";
        let answer2 = VecDeque::from([String::from("abc\"de"), String::from("\\")]);
        let line3 = "'quer\\'ty' 'asdf\\\\' \"b\\\"lah\" \"lorem\\\\\"";
        let answer3 = VecDeque::from([
            String::from("quer'ty"),
            String::from("asdf\\"),
            String::from("b\"lah"),
            String::from("lorem\\"),
        ]);

        let result1 = split(line1);
        let result2 = split(line2);
        let result3 = split(line3);

        assert_eq!(result1, Ok(answer1));
        assert_eq!(result2, Ok(answer2));
        assert_eq!(result3, Ok(answer3));
    }

    #[test]
    fn errors() {
        let line1 = "zero 'one'\"two\"";
        let answer1 = SplitError::SpacingMissing;
        let line2 = "open 'quote without close";
        let answer2 = SplitError::UnclosedQuotes;
        let line3 = "escaped at end\\";
        let answer3 = SplitError::EscapedNewline;

        let result1 = split(line1);
        let result2 = split(line2);
        let result3 = split(line3);

        assert_eq!(result1, Err(answer1));
        assert_eq!(result2, Err(answer2));
        assert_eq!(result3, Err(answer3));
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExpectedType {
    String,
    Usize,
    Date,
    Money,
}

#[derive(Debug, PartialEq)]
struct ExpectedArg {
    name: &'static str,
    expected_type: ExpectedType,
    optional: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PlanPhase {
    Required,
    Optional,
    Finished,
}

#[derive(Debug, PartialEq)]
pub struct ArgPlan {
    expected_args: Vec<ExpectedArg>,
    phase: PlanPhase,
}

impl ArgPlan {
    pub fn new() -> Self {
        Self {
            expected_args: Vec::new(),
            phase: PlanPhase::Required,
        }
    }

    pub fn begin_optional_args(&mut self) {
        match self.phase {
            PlanPhase::Required => self.phase = PlanPhase::Optional,
            PlanPhase::Optional => panic!("cannot begin optional phase of arg plan twice"),
            PlanPhase::Finished => panic!("finished arg plan cannot begin optional phase"),
        }
    }

    pub fn finish_adding_args(&mut self) {
        match self.phase {
            PlanPhase::Required | PlanPhase::Optional => self.phase = PlanPhase::Finished,
            PlanPhase::Finished => panic!("finished arg plan cannot be finished again"),
        }
    }

    pub fn add_arg(&mut self, name: &'static str, expected_type: ExpectedType) {
        if self.new_arg_is_duplicate(name) {
            panic!("arg plan got duplicate arg {:?}", name);
        }
        match self.phase {
            PlanPhase::Required => self.add_arg_internal(name, expected_type, false),
            PlanPhase::Optional => self.add_arg_internal(name, expected_type, true),
            PlanPhase::Finished => panic!("cannot add arg to finished arg plan"),
        }
    }

    fn new_arg_is_duplicate(&self, arg_name: &'static str) -> bool {
        self.expected_args.iter().any(|arg| arg.name == arg_name)
    }

    fn add_arg_internal(
        &mut self,
        name: &'static str,
        expected_type: ExpectedType,
        optional: bool,
    ) {
        let expected_arg = ExpectedArg {
            name,
            expected_type,
            optional,
        };
        self.expected_args.push(expected_arg);
    }

    pub fn min_arg_count(&self) -> usize {
        match self.phase {
            PlanPhase::Finished => self
                .expected_args
                .iter()
                .filter(|arg| !arg.optional)
                .count(),
            PlanPhase::Required | PlanPhase::Optional => {
                panic!("cannot get min arg count on unfinished arg plan");
            }
        }
    }

    pub fn max_arg_count(&self) -> usize {
        match self.phase {
            PlanPhase::Finished => self.expected_args.len(),
            PlanPhase::Required | PlanPhase::Optional => {
                panic!("cannot get max arg count on unfinished arg plan");
            }
        }
    }

    fn iter(&self) -> impl Iterator<Item = &ExpectedArg> {
        match self.phase {
            PlanPhase::Finished => self.expected_args.iter(),
            PlanPhase::Required | PlanPhase::Optional => {
                panic!("cannot iterate over unfinished arg plan");
            }
        }
    }
}

#[cfg(test)]
mod test_arg_plan {
    use super::*;

    #[test]
    fn new() {
        let expected_args: Vec<ExpectedArg> = Vec::new();
        let phase = PlanPhase::Required;

        let arg_plan = ArgPlan::new();

        assert_eq!(
            arg_plan,
            ArgPlan {
                expected_args,
                phase
            }
        );
    }

    #[test]
    fn begin_optional_args_1() {
        let mut arg_plan = ArgPlan::new();

        arg_plan.begin_optional_args();

        assert_eq!(arg_plan.phase, PlanPhase::Optional);
    }

    #[test]
    fn finish_adding_args_1() {
        let mut arg_plan_1 = ArgPlan::new();
        let mut arg_plan_2 = ArgPlan::new();
        arg_plan_2.begin_optional_args();

        arg_plan_1.finish_adding_args();
        arg_plan_2.finish_adding_args();

        assert_eq!(arg_plan_1.phase, PlanPhase::Finished);
        assert_eq!(arg_plan_2.phase, PlanPhase::Finished);
    }

    #[test]
    #[should_panic]
    fn begin_optional_args_2() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.begin_optional_args();

        arg_plan.begin_optional_args();
    }

    #[test]
    #[should_panic]
    fn begin_optional_args_3() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.begin_optional_args();
        arg_plan.finish_adding_args();

        arg_plan.begin_optional_args();
    }

    #[test]
    #[should_panic]
    fn finish_adding_args_2() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.finish_adding_args();

        arg_plan.finish_adding_args();
    }

    #[test]
    fn add_arg_1() {
        let string = ExpectedType::String;
        let expected_args: Vec<ExpectedArg> = vec![
            ExpectedArg {
                name: "arg_1",
                expected_type: string,
                optional: false,
            },
            ExpectedArg {
                name: "arg_2",
                expected_type: string,
                optional: true,
            },
        ];
        let phase = PlanPhase::Optional;
        let mut arg_plan = ArgPlan::new();

        arg_plan.add_arg("arg_1", string);
        arg_plan.begin_optional_args();
        arg_plan.add_arg("arg_2", string);

        assert_eq!(
            arg_plan,
            ArgPlan {
                expected_args,
                phase
            }
        );
    }

    #[test]
    #[should_panic]
    fn add_arg_2() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.finish_adding_args();

        arg_plan.add_arg("too_late", ExpectedType::String);
    }

    #[test]
    #[should_panic]
    fn add_arg_3() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.add_arg("duplicate", ExpectedType::String);
        arg_plan.begin_optional_args();

        arg_plan.add_arg("duplicate", ExpectedType::String);
    }

    #[test]
    fn min_arg_count_1() {
        let mut arg_plan_1 = ArgPlan::new();
        let mut arg_plan_2 = ArgPlan::new();
        arg_plan_1.add_arg("arg_1", ExpectedType::String);
        arg_plan_2.add_arg("arg_1", ExpectedType::String);
        arg_plan_2.begin_optional_args();
        arg_plan_2.add_arg("arg_2", ExpectedType::String);
        arg_plan_1.finish_adding_args();
        arg_plan_2.finish_adding_args();

        let min_args_1 = arg_plan_1.min_arg_count();
        let min_args_2 = arg_plan_2.min_arg_count();

        assert_eq!(min_args_1, 1);
        assert_eq!(min_args_2, 1);
    }

    #[test]
    #[should_panic]
    fn min_arg_count_2() {
        let arg_plan = ArgPlan::new();

        let _min_args = arg_plan.min_arg_count();
    }

    #[test]
    #[should_panic]
    fn min_arg_count_3() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.begin_optional_args();

        let _min_args = arg_plan.min_arg_count();
    }

    #[test]
    fn max_arg_count_1() {
        let mut arg_plan_1 = ArgPlan::new();
        let mut arg_plan_2 = ArgPlan::new();
        arg_plan_1.add_arg("arg_1", ExpectedType::String);
        arg_plan_2.add_arg("arg_1", ExpectedType::String);
        arg_plan_2.begin_optional_args();
        arg_plan_2.add_arg("arg_2", ExpectedType::String);
        arg_plan_1.finish_adding_args();
        arg_plan_2.finish_adding_args();

        let max_args_1 = arg_plan_1.max_arg_count();
        let max_args_2 = arg_plan_2.max_arg_count();

        assert_eq!(max_args_1, 1);
        assert_eq!(max_args_2, 2);
    }

    #[test]
    #[should_panic]
    fn max_arg_count_2() {
        let arg_plan = ArgPlan::new();

        let _max_args = arg_plan.max_arg_count();
    }

    #[test]
    #[should_panic]
    fn max_arg_count_3() {
        let mut arg_plan = ArgPlan::new();
        arg_plan.begin_optional_args();

        let _max_args = arg_plan.max_arg_count();
    }
}

#[derive(Debug)]
pub enum ArgError {
    TooFew(usize),
    TooMany(usize),
}

impl Display for ArgError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TooFew(n) => write!(f, "at least {} argument(s) are required", n),
            Self::TooMany(n) => write!(f, "no more than {} argument(s) are allowed", n),
        }
    }
}

impl Error for ArgError {}

#[derive(Debug)]
pub enum ParsedValue {
    String(String),
    OptionString(Option<String>),
    Usize(usize),
    OptionUsize(Option<usize>),
    Date(Date),
    OptionDate(Option<Date>),
    Money(Money),
    OptionMoney(Option<Money>),
    Invalid(Box<dyn Error>),
}

impl PartialEq for ParsedValue {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::String(s1), Self::String(s2)) => s1 == s2,
            (Self::OptionString(os1), Self::OptionString(os2)) => os1 == os2,
            (Self::Usize(u1), Self::Usize(u2)) => u1 == u2,
            (Self::OptionUsize(ou1), Self::OptionUsize(ou2)) => ou1 == ou2,
            (Self::Date(d1), Self::Date(d2)) => d1 == d2,
            (Self::OptionDate(od1), Self::OptionDate(od2)) => od1 == od2,
            (Self::Money(m1), Self::Money(m2)) => m1 == m2,
            (Self::OptionMoney(om1), Self::OptionMoney(om2)) => om1 == om2,
            (Self::Invalid(_e1), Self::Invalid(_e2)) => false,
            (_, _) => false,
        }
    }
}

impl ParsedValue {
    fn new_invalid<E: Error + 'static>(error: E) -> Self {
        Self::Invalid(Box::new(error))
    }

    fn new_required(arg: String, expected_type: ExpectedType) -> Self {
        match expected_type {
            ExpectedType::String => Self::String(arg),
            ExpectedType::Usize => match arg.parse() {
                Ok(u) => Self::Usize(u),
                Err(e) => Self::new_invalid(e),
            },
            ExpectedType::Date => match arg.parse() {
                Ok(date) => Self::Date(date),
                Err(e) => Self::new_invalid(e),
            },
            ExpectedType::Money => match arg.parse() {
                Ok(money) => Self::Money(money),
                Err(e) => Self::new_invalid(e),
            },
        }
    }

    fn new_optional(arg: Option<String>, expected_type: ExpectedType) -> Self {
        match expected_type {
            ExpectedType::String => Self::OptionString(arg),
            ExpectedType::Usize => match arg.map(|arg| arg.parse()) {
                Some(Ok(u)) => Self::OptionUsize(Some(u)),
                None => Self::OptionUsize(None),
                Some(Err(e)) => Self::new_invalid(e),
            },
            ExpectedType::Date => match arg.map(|arg| arg.parse()) {
                Some(Ok(date)) => Self::OptionDate(Some(date)),
                None => Self::OptionDate(None),
                Some(Err(e)) => Self::new_invalid(e),
            },
            ExpectedType::Money => match arg.map(|arg| arg.parse()) {
                Some(Ok(money)) => Self::OptionMoney(Some(money)),
                None => Self::OptionMoney(None),
                Some(Err(e)) => Self::new_invalid(e),
            },
        }
    }
}

impl ParsedValue {
    fn get_string(self) -> Result<String, Box<dyn Error>> {
        match self {
            Self::String(string) => Ok(string),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_string called on parsed value of another type"),
        }
    }

    fn get_option_string(self) -> Result<Option<String>, Box<dyn Error>> {
        match self {
            Self::OptionString(option_string) => Ok(option_string),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_option_string called on parsed value of another type"),
        }
    }

    fn get_usize(self) -> Result<usize, Box<dyn Error>> {
        match self {
            Self::Usize(u) => Ok(u),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_usize called on parsed value of another type"),
        }
    }

    fn get_option_usize(self) -> Result<Option<usize>, Box<dyn Error>> {
        match self {
            Self::OptionUsize(option_u) => Ok(option_u),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_option_usize called on parsed value of another type"),
        }
    }

    fn get_date(self) -> Result<Date, Box<dyn Error>> {
        match self {
            Self::Date(date) => Ok(date),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_date called on parsed value of another type"),
        }
    }

    fn get_option_date(self) -> Result<Option<Date>, Box<dyn Error>> {
        match self {
            Self::OptionDate(option_date) => Ok(option_date),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_option_date called on parsed value of another type"),
        }
    }

    fn get_money(self) -> Result<Money, Box<dyn Error>> {
        match self {
            Self::Money(money) => Ok(money),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_money called on parsed value of another type"),
        }
    }

    fn get_option_money(self) -> Result<Option<Money>, Box<dyn Error>> {
        match self {
            Self::OptionMoney(option_money) => Ok(option_money),
            Self::Invalid(error) => Err(error),
            _ => panic!("get_option_money called on parsed value of another type"),
        }
    }
}

#[derive(Debug, PartialEq)]
struct ParsedArg {
    name: &'static str,
    value: ParsedValue,
}

#[derive(Debug, PartialEq)]
pub struct ArgMap {
    parsed_args: VecDeque<ParsedArg>,
    filled: bool,
}

impl ArgMap {
    pub fn new() -> Self {
        Self {
            parsed_args: VecDeque::new(),
            filled: false,
        }
    }

    pub fn insert(&mut self, name: &'static str, value: ParsedValue) {
        if self.filled {
            panic!("cannot insert another arg into filled arg map");
        }
        if self.has_arg(name) {
            panic!("cannot insert duplicate arg {:?} into arg map", name);
        }

        let parsed_arg = ParsedArg { name, value };
        self.parsed_args.push_back(parsed_arg);
    }

    fn has_arg(&self, name: &'static str) -> bool {
        self.parsed_args.iter().any(|arg| arg.name == name)
    }

    pub fn finish_filling(&mut self) {
        if self.filled {
            panic!("cannot finish filling arg map that is already filled");
        } else {
            self.filled = true;
        }
    }

    fn is_not_empty(&self) -> bool {
        !self.parsed_args.is_empty()
    }

    fn discard(&mut self) {
        self.parsed_args.clear();
    }
}

impl Drop for ArgMap {
    fn drop(&mut self) {
        if self.filled && self.is_not_empty() {
            panic!("filled arg map was dropped without being emptied");
        }
    }
}

impl ArgMap {
    pub fn construct(arg_plan: &ArgPlan, args: VecDeque<String>) -> Result<ArgMap, ArgError> {
        let mut expected_args = arg_plan.iter();
        let mut actual_args = args.into_iter();
        let mut arg_map = ArgMap::new();

        loop {
            let expected_arg = expected_args.next();
            let actual_arg = actual_args.next();

            match (expected_arg, actual_arg) {
                (Some(expected), Some(actual)) => {
                    let parsed_value = if expected.optional {
                        ParsedValue::new_optional(Some(actual), expected.expected_type)
                    } else {
                        ParsedValue::new_required(actual, expected.expected_type)
                    };
                    arg_map.insert(expected.name, parsed_value);
                }

                (Some(expected), None) => {
                    let parsed_value = if expected.optional {
                        ParsedValue::new_optional(None, expected.expected_type)
                    } else {
                        return Err(ArgError::TooFew(arg_plan.min_arg_count()));
                    };
                    arg_map.insert(expected.name, parsed_value);
                }

                (None, Some(_actual)) => {
                    return Err(ArgError::TooMany(arg_plan.max_arg_count()));
                }

                (None, None) => {
                    break;
                }
            }
        }

        arg_map.finish_filling();
        Ok(arg_map)
    }

    fn get_value(&mut self, name: &'static str) -> ParsedValue {
        if !self.filled {
            panic!("cannot get value from arg map that is not filled");
        }
        let parsed_arg = match self.parsed_args.pop_front() {
            Some(parsed) => parsed,
            None => panic!("cannot get value from empty arg map"),
        };
        if parsed_arg.name != name {
            panic!(
                "requested arg {:?} from arg map when {:?} should be next",
                name, parsed_arg.name
            );
        }
        parsed_arg.value
    }

    pub fn get_string(&mut self, name: &'static str) -> Result<String, Box<dyn Error>> {
        self.get_value(name).get_string()
    }

    pub fn get_option_string(
        &mut self,
        name: &'static str,
    ) -> Result<Option<String>, Box<dyn Error>> {
        self.get_value(name).get_option_string()
    }

    pub fn get_usize(&mut self, name: &'static str) -> Result<usize, Box<dyn Error>> {
        self.get_value(name).get_usize()
    }

    pub fn get_option_usize(
        &mut self,
        name: &'static str,
    ) -> Result<Option<usize>, Box<dyn Error>> {
        self.get_value(name).get_option_usize()
    }

    pub fn get_date(&mut self, name: &'static str) -> Result<Date, Box<dyn Error>> {
        self.get_value(name).get_date()
    }

    pub fn get_option_date(&mut self, name: &'static str) -> Result<Option<Date>, Box<dyn Error>> {
        self.get_value(name).get_option_date()
    }

    pub fn get_money(&mut self, name: &'static str) -> Result<Money, Box<dyn Error>> {
        self.get_value(name).get_money()
    }

    pub fn get_option_money(
        &mut self,
        name: &'static str,
    ) -> Result<Option<Money>, Box<dyn Error>> {
        self.get_value(name).get_option_money()
    }
}

#[cfg(test)]
mod test_arg_map {
    use super::*;

    #[test]
    fn new() {
        let parsed_args = VecDeque::new();
        let filled = false;

        let arg_map = ArgMap::new();

        assert_eq!(
            arg_map,
            ArgMap {
                parsed_args,
                filled
            }
        );
    }

    #[test]
    fn insert_1() {
        let name = "arg_A";
        let value = String::from("arg_value");
        let parsed_value_1 = ParsedValue::String(value.clone());
        let parsed_value_2 = ParsedValue::String(value.clone());
        let mut arg_map = ArgMap::new();
        let parsed_args = VecDeque::from([ParsedArg {
            name,
            value: parsed_value_1,
        }]);
        let filled = false;

        arg_map.insert(name, parsed_value_2);

        assert_eq!(
            arg_map,
            ArgMap {
                parsed_args,
                filled
            }
        );
    }

    #[test]
    #[should_panic]
    fn insert_2() {
        let name = "arg_A";
        let value = String::from("arg_value");
        let parsed_value_1 = ParsedValue::String(value.clone());
        let parsed_value_2 = ParsedValue::String(value.clone());
        let mut arg_map = ArgMap::new();
        arg_map.insert(name, parsed_value_1);

        arg_map.insert(name, parsed_value_2);
    }

    #[test]
    fn finish_filling_1() {
        let mut arg_map = ArgMap::new();
        let parsed_args = VecDeque::new();
        let filled = true;

        arg_map.finish_filling();

        assert_eq!(
            arg_map,
            ArgMap {
                parsed_args,
                filled
            }
        );
    }

    #[test]
    #[should_panic]
    fn finish_filling_2() {
        let mut arg_map = ArgMap::new();
        arg_map.finish_filling();

        arg_map.finish_filling();
    }

    #[test]
    fn construct() {
        let name_1 = "thing_1";
        let name_2 = "thing_2";
        let arg_plan = {
            let mut arg_plan = ArgPlan::new();
            arg_plan.add_arg(name_1, ExpectedType::String);
            arg_plan.begin_optional_args();
            arg_plan.add_arg(name_2, ExpectedType::String);
            arg_plan.finish_adding_args();
            arg_plan
        };
        let value_1 = String::from("value_1");
        let value_2 = String::from("value_2");
        let args_1 = VecDeque::from([value_1.clone()]);
        let args_2 = VecDeque::from([value_1.clone(), value_2.clone()]);
        let parsed_value_1 = ParsedValue::String(value_1.clone());
        let parsed_value_2 = ParsedValue::OptionString(None);
        let parsed_args_1 = VecDeque::from([
            ParsedArg {
                name: name_1,
                value: parsed_value_1,
            },
            ParsedArg {
                name: name_2,
                value: parsed_value_2,
            },
        ]);
        let parsed_value_1 = ParsedValue::String(value_1.clone());
        let parsed_value_2 = ParsedValue::OptionString(Some(value_2.clone()));
        let parsed_args_2 = VecDeque::from([
            ParsedArg {
                name: name_1,
                value: parsed_value_1,
            },
            ParsedArg {
                name: name_2,
                value: parsed_value_2,
            },
        ]);
        let filled = true;
        let mut example_arg_map_1 = ArgMap {
            parsed_args: parsed_args_1,
            filled,
        };
        let mut example_arg_map_2 = ArgMap {
            parsed_args: parsed_args_2,
            filled,
        };

        let mut arg_map_1 = ArgMap::construct(&arg_plan, args_1).expect("result is not err");
        let mut arg_map_2 = ArgMap::construct(&arg_plan, args_2).expect("result is not err");

        assert_eq!(arg_map_1, example_arg_map_1);
        assert_eq!(arg_map_2, example_arg_map_2);

        arg_map_1.discard();
        arg_map_2.discard();
        example_arg_map_1.discard();
        example_arg_map_2.discard();
    }

    #[test]
    fn get_string() {
        let name = "string_arg";
        let arg_plan = {
            let mut arg_plan = ArgPlan::new();
            arg_plan.add_arg(name, ExpectedType::String);
            arg_plan.finish_adding_args();
            arg_plan
        };
        let value = String::from("string_value");
        let args = VecDeque::from([value.clone()]);
        let mut arg_map = ArgMap::construct(&arg_plan, args).expect("result is not err");

        let string = arg_map.get_string(name).expect("result is not err");

        assert_eq!(string, value);
    }

    #[test]
    fn get_option_string() {
        let name = "opt_string_arg";
        let arg_plan = {
            let mut arg_plan = ArgPlan::new();
            arg_plan.begin_optional_args();
            arg_plan.add_arg(name, ExpectedType::String);
            arg_plan.finish_adding_args();
            arg_plan
        };
        let value = String::from("string_value");
        let args_1 = VecDeque::from([value.clone()]);
        let args_2 = VecDeque::from([]);
        let mut arg_map_1 = ArgMap::construct(&arg_plan, args_1).expect("result is not err");
        let mut arg_map_2 = ArgMap::construct(&arg_plan, args_2).expect("result is not err");

        let opt_string_1 = arg_map_1
            .get_option_string(name)
            .expect("result is not err");
        let opt_string_2 = arg_map_2
            .get_option_string(name)
            .expect("result is not err");

        assert_eq!(opt_string_1, Some(value));
        assert_eq!(opt_string_2, None);
    }
}
