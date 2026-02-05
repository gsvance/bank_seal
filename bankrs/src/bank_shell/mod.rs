use std::collections::VecDeque;
use std::error::Error;
use std::fmt::Display;
use std::io::{self, Write};

mod args;
mod commands;
mod replies;

pub use commands::Command;
pub use replies::Reply;

const PROMPT: &'static str = "$> ";
const WELCOME: &'static str = "\
    Welcome to the bankrs shell!\n\
    Type 'help' or another command";

pub struct BankShell {
    // The bank shell struct is sort of a pure object-oriented abstraction
    // It contains no data and exists only as a way to encapsulate behavior
    // If it ever *needs* any data, then the data can certainly go here
}

impl BankShell {
    pub fn start() -> Self {
        let shell = Self {};
        shell.show_welcome_message();
        shell
    }

    pub fn show_output<T: Display>(&self, output: T) {
        let mut string = output.to_string();
        if string != "" {
            string.push_str("\n\n");
        } else {
            string.push('\n');
        }
        print!("{}", string);
    }

    fn show_welcome_message(&self) {
        self.show_output(WELCOME);
    }

    fn show_prompt(&self) -> Result<(), Box<dyn Error>> {
        print!("{}", PROMPT);
        io::stdout().flush()?;
        Ok(())
    }

    pub fn get_args(&self) -> Result<VecDeque<String>, Box<dyn Error>> {
        self.show_prompt()?;
        let line = self.get_line()?;
        Ok(args::split(&line)?)
    }

    fn get_line(&self) -> Result<String, Box<dyn Error>> {
        let mut line = String::new();
        io::stdin().read_line(&mut line)?;
        Ok(line)
    }
}
