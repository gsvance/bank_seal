use std::collections::VecDeque;
use std::error::Error;

use lazy_static;

use super::args::{ArgMap, ArgPlan, ExpectedType};
use crate::program_data::{Date, Money};

lazy_static::lazy_static! {

    // System commands

    static ref SAVE_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.finish_adding_args();
        args
    };

    static ref CONFIG_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("key", ExpectedType::String);
        args.begin_optional_args();
        args.add_arg("value", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref EXIT_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.finish_adding_args();
        args
    };

    // Ledger commands

    static ref ADD_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("date", ExpectedType::Date);
        args.add_arg("merchant_name_or_id", ExpectedType::String);
        args.add_arg("amount", ExpectedType::Money);
        args.begin_optional_args();
        args.add_arg("note", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref DEL_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("unparsed_id", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref REC_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.begin_optional_args();
        args.add_arg("how_many", ExpectedType::Usize);
        args.finish_adding_args();
        args
    };

    // Merchants commands

    static ref MER_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("name_or_id", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref EST_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("full_name", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref DEMO_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("name_or_id", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref RENO_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("name_or_id", ExpectedType::String);
        args.add_arg("new_full_name", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref NICK_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("name_or_id", ExpectedType::String);
        args.add_arg("nickname", ExpectedType::String);
        args.finish_adding_args();
        args
    };

    static ref DENK_ARGS: ArgPlan = {
        let mut args = ArgPlan::new();
        args.add_arg("nickname", ExpectedType::String);
        args.finish_adding_args();
        args
    };
}

#[derive(Clone, Copy)]
enum Identifier {
    // System commands
    Save,
    Configure,
    Exit,

    // Ledger commands
    Add,
    Delete,
    Recent,

    // Merchants commands
    Merchant,
    Establish,
    Demolish,
    Renovate,
    Nickname,
    DeNickname,
}

impl Identifier {
    fn new(name: &str) -> Option<Self> {
        match name {
            // System commands
            "save" => Some(Self::Save),
            "config" => Some(Self::Configure),
            "exit" => Some(Self::Exit),

            // Ledger commands
            "add" => Some(Self::Add),
            "del" => Some(Self::Delete),
            "rec" => Some(Self::Recent),

            // Merchants commands
            "mer" => Some(Self::Merchant),
            "est" => Some(Self::Establish),
            "demo" => Some(Self::Demolish),
            "reno" => Some(Self::Renovate),
            "nick" => Some(Self::Nickname),
            "denk" => Some(Self::DeNickname),

            // None of the above
            _ => None,
        }
    }

    fn retrieve_arg_plan(self) -> &'static ArgPlan {
        match self {
            // System commands
            Self::Save => &SAVE_ARGS,
            Self::Configure => &CONFIG_ARGS,
            Self::Exit => &EXIT_ARGS,

            // Ledger commands
            Self::Add => &ADD_ARGS,
            Self::Delete => &DEL_ARGS,
            Self::Recent => &REC_ARGS,

            // Merchants commands
            Self::Merchant => &MER_ARGS,
            Self::Establish => &EST_ARGS,
            Self::Demolish => &DEMO_ARGS,
            Self::Renovate => &RENO_ARGS,
            Self::Nickname => &NICK_ARGS,
            Self::DeNickname => &DENK_ARGS,
        }
    }
}

pub enum Command {
    // System commands
    //Help,
    Save,
    Configure {
        key: String,
        value: Option<String>,
    },
    Exit,
    ArgumentError {
        error: Box<dyn Error>,
    },
    UnknownCommand {
        command: String,
    },
    Nothing,

    // Ledger commands
    Add {
        date: Date,
        merchant_name_or_id: String,
        amount: Money,
        note: Option<String>,
    },
    Delete {
        unparsed_id: String,
    },
    //Edit,
    Recent {
        how_many: Option<usize>,
    },
    //Find,
    //Statement,
    //Categorize,

    // Merchants commands
    Merchant {
        name_or_id: String,
    },
    Establish {
        full_name: String,
    },
    Demolish {
        name_or_id: String,
    },
    Renovate {
        name_or_id: String,
        new_full_name: String,
    },
    Nickname {
        name_or_id: String,
        nickname: String,
    },
    DeNickname {
        nickname: String,
    },
}

impl Command {
    pub fn new(mut args: VecDeque<String>) -> Self {
        let command_name = match args.pop_front() {
            Some(name) => name,
            None => return Self::Nothing,
        };

        match Identifier::new(&command_name) {
            Some(identifier) => match Self::parse_args(identifier, args) {
                Ok(command) => command,
                Err(error) => Self::ArgumentError { error },
            },
            None => Self::UnknownCommand {
                command: command_name,
            },
        }
    }

    fn parse_args(identifier: Identifier, args: VecDeque<String>) -> Result<Self, Box<dyn Error>> {
        let arg_plan = identifier.retrieve_arg_plan();
        let mut arg_map = ArgMap::construct(arg_plan, args)?;

        match identifier {
            // System commands
            Identifier::Save => Ok(Self::Save),

            Identifier::Configure => {
                let key = arg_map.get_string("key")?;
                let value = arg_map.get_option_string("value")?;
                Ok(Self::Configure { key, value })
            }

            Identifier::Exit => Ok(Self::Exit),

            // Ledger commands
            Identifier::Add => {
                let date = arg_map.get_date("date")?;
                let merchant_name_or_id = arg_map.get_string("merchant_name_or_id")?;
                let amount = arg_map.get_money("amount")?;
                let note = arg_map.get_option_string("note")?;
                Ok(Self::Add {
                    date,
                    merchant_name_or_id,
                    amount,
                    note,
                })
            }

            Identifier::Delete => {
                let unparsed_id = arg_map.get_string("unparsed_id")?;
                Ok(Self::Delete { unparsed_id })
            }

            Identifier::Recent => {
                let how_many = arg_map.get_option_usize("how_many")?;
                Ok(Self::Recent { how_many })
            }

            // Merchants commands
            Identifier::Merchant => {
                let name_or_id = arg_map.get_string("name_or_id")?;
                Ok(Self::Merchant { name_or_id })
            }

            Identifier::Establish => {
                let full_name = arg_map.get_string("full_name")?;
                Ok(Self::Establish { full_name })
            }

            Identifier::Demolish => {
                let name_or_id = arg_map.get_string("name_or_id")?;
                Ok(Self::Demolish { name_or_id })
            }

            Identifier::Renovate => {
                let name_or_id = arg_map.get_string("name_or_id")?;
                let new_full_name = arg_map.get_string("new_full_name")?;
                Ok(Self::Renovate {
                    name_or_id,
                    new_full_name,
                })
            }

            Identifier::Nickname => {
                let name_or_id = arg_map.get_string("name_or_id")?;
                let nickname = arg_map.get_string("nickname")?;
                Ok(Self::Nickname {
                    name_or_id,
                    nickname,
                })
            }

            Identifier::DeNickname => {
                let nickname = arg_map.get_string("nickname")?;
                Ok(Self::DeNickname { nickname })
            }
        }
    }
}
