use std::error::Error;
use std::fmt::{self, Display};
use std::path;

use lazy_static;

lazy_static::lazy_static! {
    static ref THIS_FILE: path::PathBuf = {
        let this_file = path::PathBuf::from(file!());
        this_file.canonicalize().expect("abs path to this src file should exist")
    };

    static ref SRC_DIR: path::PathBuf = {
        THIS_FILE.parent().expect("parent src dir should exist").to_path_buf()
    };

    static ref PROJECT_DIR: path::PathBuf = {
        SRC_DIR.parent().expect("parent project dir should exist").to_path_buf()
    };

    pub static ref DATA_DIR: path::PathBuf = {
        let mut data_dir = PROJECT_DIR.clone();
        data_dir.push("user_data");
        data_dir.canonicalize().expect("project data dir should exist")
    };
}

#[derive(Debug)]
enum InvalidName {
    Empty,
    BadChar(char),
}

impl Display for InvalidName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Empty => write!(f, "a name string cannot be empty"),
            Self::BadChar(c) => write!(f, "illegal character {:?} in name string", c),
        }
    }
}

impl Error for InvalidName {}

fn is_valid_name_char(c: char) -> bool {
    c.is_ascii_alphanumeric() || c == '_'
}

fn validate_name(name: &str) -> Result<(), InvalidName> {
    if name == "" {
        return Err(InvalidName::Empty);
    }

    for c in name.chars() {
        if !is_valid_name_char(c) {
            return Err(InvalidName::BadChar(c));
        }
    }

    Ok(())
}

fn assemble_path(name: &str, suffix: &str) -> Result<path::PathBuf, Box<dyn Error>> {
    validate_name(name)?;
    let mut file_name = String::from(name);
    file_name.push_str(suffix);

    let mut file_path = DATA_DIR.clone();
    file_path.push(file_name);
    Ok(file_path)
}

const CONFIG_SUFFIX: &'static str = "_config.json";
const LEDGER_SUFFIX: &'static str = "_ledger.json";
const MERCHANTS_SUFFIX: &'static str = "_merchants.json";

pub fn assemble_config_path(config_name: &str) -> Result<path::PathBuf, Box<dyn Error>> {
    assemble_path(config_name, CONFIG_SUFFIX)
}

pub fn assemble_ledger_path(ledger_name: &str) -> Result<path::PathBuf, Box<dyn Error>> {
    assemble_path(ledger_name, LEDGER_SUFFIX)
}

pub fn assemble_merchants_path(merchants_name: &str) -> Result<path::PathBuf, Box<dyn Error>> {
    assemble_path(merchants_name, MERCHANTS_SUFFIX)
}
