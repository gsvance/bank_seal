use std::error::Error;
use std::fmt::{self, Display};

use crate::tables;
use tables::Table;

pub enum Reply {
    Empty,
    StaticMessage(&'static str),
    ShortMessage(String),
    LongMessage(Vec<String>),
    ErrorMessage(Box<dyn Error>),
    TableData(Box<dyn Table>),
}

impl Reply {}

impl Display for Reply {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Empty => write!(f, ""),
            Self::StaticMessage(static_str) => write!(f, "{}", static_str),
            Self::ShortMessage(line) => write!(f, "{}", line),
            Self::LongMessage(lines) => write!(f, "{}", lines.join("\n")),
            Self::ErrorMessage(error) => write!(f, "Error: {}", error),
            Self::TableData(data) => write!(f, "{}\n", data.tabulate()),
        }
    }
}
