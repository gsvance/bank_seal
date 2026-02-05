use std::error::Error;

mod bank_shell;
mod command_line_args;
mod paths;
mod program_data;
mod tables;

use bank_shell::BankShell;
use bank_shell::Command as ShellCommand;

pub use command_line_args::CommandLineArgs;
use program_data::ProgramData;

pub fn run(command_line_args: CommandLineArgs) -> Result<(), Box<dyn Error>> {
    let shell = BankShell::start();
    let mut data = ProgramData::load(command_line_args)?;

    loop {
        let shell_args = shell.get_args()?;
        let shell_command = ShellCommand::new(shell_args);
        let shell_reply = data.execute(shell_command);
        shell.show_output(shell_reply);

        if data.exiting() {
            break;
        }
    }

    Ok(())
}
