use std::default::Default;
use std::error::Error;
use std::fmt::{self, Display};
use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json;

use crate::paths;

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    name: String,
    description: String,
    ledger_name: String,
    merchants_name: String,
    //split_money_column,
    //starting_balance,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            name: String::from("DEFAULT_CONFIG_NAME"),
            description: String::from("DEFAULT_DESCRIPTION_TEXT"),
            ledger_name: String::from("DEFAULT_LEDGER_NAME"),
            merchants_name: String::from("DEFAULT_MERCHANTS_NAME"),
        }
    }
}

impl Config {
    pub fn initialize(name: &str, new: bool) -> Result<Self, Box<dyn Error>> {
        if new {
            Self::create_new_on_disk(name)?;
        }
        Self::load_from_disk(name)
    }
}

#[derive(Debug)]
pub enum ConfigError {
    ConfigAlreadyExists,
}

impl Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ConfigAlreadyExists => {
                write!(f, "configuration file with that name already exists")
            }
        }
    }
}

impl Error for ConfigError {}

impl Config {
    fn create_new_on_disk(name: &str) -> Result<(), Box<dyn Error>> {
        let mut config = Self::default();
        config.name = String::from(name);
        let config_path = paths::assemble_config_path(name)?;
        if let Ok(false) = config_path.try_exists() {
            config.write_file(config_path)
        } else {
            Err(Box::new(ConfigError::ConfigAlreadyExists))
        }
    }

    fn load_from_disk(name: &str) -> Result<Self, Box<dyn Error>> {
        let config_path = paths::assemble_config_path(name)?;
        Self::read_file(config_path)
    }

    fn rename_on_disk(old_name: &str, new_name: &str) -> Result<(), Box<dyn Error>> {
        let old_path = paths::assemble_config_path(old_name)?;
        let mut config = Self::read_file(old_path.clone())?;
        config.name = String::from(new_name);
        let new_path = paths::assemble_config_path(new_name)?;
        if let Ok(false) = new_path.try_exists() {
            config.write_file(new_path)?;
            Self::delete_file(old_path)
        } else {
            Err(Box::new(ConfigError::ConfigAlreadyExists))
        }
    }
}

impl Config {
    fn write_file(&self, file_path: PathBuf) -> Result<(), Box<dyn Error>> {
        let file = File::create(file_path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer(writer, self)?;
        Ok(())
    }

    fn read_file(file_path: PathBuf) -> Result<Self, Box<dyn Error>> {
        let file = File::open(file_path)?;
        let reader = BufReader::new(file);
        Ok(serde_json::from_reader(reader)?)
    }

    fn delete_file(file_path: PathBuf) -> Result<(), Box<dyn Error>> {
        Ok(fs::remove_file(file_path)?)
    }
}

impl Config {
    pub fn configure(&mut self, key: String, value: Option<String>) -> String {
        let old_value: &str = match key.as_ref() {
            "name" => &self.name,
            "description" => &self.description,
            "ledger_name" => &self.ledger_name,
            "merchants_name" => &self.merchants_name,
            _ => {
                return format!("Unknown configuration key: {:?}", key);
            }
        };

        let mut output = String::from("Configuration ");
        output.push_str(&key);
        output.push_str(" = ");
        output.push_str(&format!("{:?}", old_value));

        if let Some(new_value) = value {
            output.push_str(" -> ");
            output.push_str(&format!("{:?}", new_value));
            match key.as_ref() {
                "name" => {
                    match Self::rename_on_disk(&self.name, &new_value) {
                        Ok(()) => {}
                        Err(error) => return error.to_string(),
                    }
                    self.name = new_value;
                }
                "description" => self.description = new_value,
                "ledger_name" => self.ledger_name = new_value,
                "merchants_name" => self.merchants_name = new_value,
                _ => unreachable!(),
            }
        }

        output
    }
}

/*
impl Config {
    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn description(&self) -> &str {
        &self.description
    }

    pub fn ledger_name(&self) -> &str {
        &self.ledger_name
    }

    pub fn merchants_name(&self) -> &str {
        &self.merchants_name
    }
}
*/

impl Config {
    pub fn ledger_path(&self) -> Result<PathBuf, Box<dyn Error>> {
        paths::assemble_ledger_path(&self.ledger_name)
    }

    pub fn merchants_path(&self) -> Result<PathBuf, Box<dyn Error>> {
        paths::assemble_merchants_path(&self.merchants_name)
    }
}
