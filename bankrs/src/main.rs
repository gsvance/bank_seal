extern crate bankrs;

use std::env;
use std::process;

fn main() {
    let arg_result = bankrs::CommandLineArgs::new(env::args());
    let args = arg_result.unwrap_or_else(|error| {
        eprintln!("Command line error: {}", error);
        process::exit(1);
    });

    let run_result = bankrs::run(args);
    if let Err(error) = run_result {
        eprintln!("Error running application: {}", error);
        process::exit(2);
    }
}
