pub struct CommandLineArgs {
    config_name: String,
    new_config: bool,
    // TODO: add one-off commands here
}

impl CommandLineArgs {
    pub fn new<T>(mut args: T) -> Result<Self, String>
    where
        T: Iterator<Item = String>,
    {
        // TODO: replace the body of this function with a real argparser

        let mut config_name = None;
        let mut new_config = false;

        args.next(); // Throw away the program name

        for arg in args {
            if arg == "-n" || arg == "--new_config" {
                new_config = true;
            } else if config_name.is_none() {
                config_name = Some(arg);
            } else {
                return Err(String::from("too many arguments"));
            }
        }

        let config_name = config_name.ok_or(String::from("config name is required"))?;
        Ok(Self {
            config_name,
            new_config,
        })
    }

    pub fn config_name(&self) -> &str {
        &self.config_name
    }

    pub fn new_config(&self) -> bool {
        self.new_config
    }
}
