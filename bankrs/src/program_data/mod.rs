use std::error::Error;

mod config;
mod hex_id;
mod ledger;
mod merchants;

use config::Config;
pub use ledger::{Date, Money};
use ledger::{Ledger, Transaction, LedgerRow};
use merchants::{Merchants, Merchant};

use crate::command_line_args;
use command_line_args::CommandLineArgs;

use crate::bank_shell;
use bank_shell::Command as ShellCommand;
use bank_shell::Reply as ShellReply;

use crate::tables;
use tables::{TableRow, ColumnSpec, Alignment};

pub struct ProgramStatus {
    exit_flag: bool,
    // TODO: Add some other stuff, like an unsaved data flag
}

pub struct ProgramData {
    status: ProgramStatus,
    config: Config,
    ledger: Ledger,
    merchants: Merchants,
}

impl ProgramData {
    pub fn load(command_line_args: CommandLineArgs) -> Result<Self, Box<dyn Error>> {
        let status = ProgramStatus { exit_flag: false };

        let config = Config::initialize(
            command_line_args.config_name(),
            command_line_args.new_config(),
        )?;

        let ledger_path = config.ledger_path()?;
        let ledger = if ledger_path.try_exists()? {
            Ledger::from_file(ledger_path)?
        } else {
            Ledger::new()
        };

        let merchants_path = config.merchants_path()?;
        let merchants = if merchants_path.try_exists()? {
            Merchants::from_file(merchants_path)?
        } else {
            Merchants::new()
        };

        Ok(Self {
            status,
            config,
            ledger,
            merchants,
        })
    }

    pub fn execute(&mut self, command: ShellCommand) -> ShellReply {
        match command {
            // System commands
            ShellCommand::Save => self.save_data(),

            ShellCommand::Configure { key, value } => {
                let output = self.config.configure(key, value);
                ShellReply::ShortMessage(output)
            }

            ShellCommand::Exit => {
                self.status.exit_flag = true;
                ShellReply::StaticMessage("Exiting program...")
            }

            ShellCommand::ArgumentError { error } => {
                ShellReply::ShortMessage(format!("Argument error: {}", error))
            }

            ShellCommand::UnknownCommand { command } => {
                ShellReply::ShortMessage(format!("Unknown command: {:?}", command))
            }

            ShellCommand::Nothing => ShellReply::Empty,

            // Ledger commands
            ShellCommand::Add {
                date,
                merchant_name_or_id,
                amount,
                note,
            } => self.add_transaction(date, merchant_name_or_id, amount, note),

            ShellCommand::Delete { unparsed_id } => self.delete_transaction(unparsed_id),

            ShellCommand::Recent { how_many } => self.recent_transactions(how_many),

            // Merchants commands
            ShellCommand::Merchant { name_or_id } => self.display_merchant(name_or_id),

            ShellCommand::Establish { full_name } => self.establish_merchant(full_name),

            ShellCommand::Demolish { name_or_id } => self.demolish_merchant(name_or_id),

            ShellCommand::Renovate {
                name_or_id,
                new_full_name,
            } => self.renovate_merchant(name_or_id, new_full_name),

            ShellCommand::Nickname {
                name_or_id,
                nickname,
            } => self.nickname_merchant(name_or_id, nickname),

            ShellCommand::DeNickname { nickname } => self.de_nickname_merchant(nickname),
        }
    }

    pub fn exiting(&self) -> bool {
        self.status.exit_flag
    }
}

impl ProgramData {
    fn save_data(&self) -> ShellReply {
        let ledger_path = match self.config.ledger_path() {
            Ok(path) => path,
            Err(error) => return ShellReply::ErrorMessage(error),
        };
        let merchants_path = match self.config.merchants_path() {
            Ok(path) => path,
            Err(error) => return ShellReply::ErrorMessage(error),
        };
        if let Err(error) = self.ledger.to_file(ledger_path) {
            return ShellReply::ErrorMessage(error);
        }
        if let Err(error) = self.merchants.to_file(merchants_path) {
            return ShellReply::ErrorMessage(error);
        }
        ShellReply::StaticMessage("Ledger and merchants data saved")
    }
}

pub struct LedgerLine<'r, 't, 'm> {
    row: &'r LedgerRow,
    transaction: &'t Transaction,
    merchant: &'m Merchant,
}

impl<'r, 't, 'm> LedgerLine<'r, 't, 'm> {
    fn new(
        row: &'r LedgerRow,
        transaction: &'t Transaction,
        merchant: &'m Merchant
    ) -> Self {
        Self { row, transaction, merchant }
    }
}

impl TableRow for LedgerLine<'_, '_, '_> {
    const NUM_COLUMNS: usize = 6;

    fn column_specs_unchecked() -> Vec<ColumnSpec<Self>> {
        vec![
            ColumnSpec::new(
                "ID",
                Alignment::Center,
                Box::new(|line: &LedgerLine| line.row.id().to_string())
            ),
            ColumnSpec::new(
                "Date",
                Alignment::Right,
                Box::new(|line: &LedgerLine| line.transaction.date().to_string())
            ),
            ColumnSpec::new(
                "Merchant",
                Alignment::Left,
                Box::new(|line: &LedgerLine| line.merchant.full_name().to_string())
            ),
            ColumnSpec::new(
                "Amount",
                Alignment::Right,
                Box::new(|line: &LedgerLine| line.transaction.amount().to_string())
            ),
            ColumnSpec::new(
                "Subtotal",
                Alignment::Right,
                Box::new(|line: &LedgerLine| {
                    line.row
                        .subtotal()
                        .map(|money| money.to_string())
                        .unwrap_or_else(String::new)
                    }
                )
            ),
            ColumnSpec::new(
                "Note",
                Alignment::Left,
                Box::new(|line: &LedgerLine| line.transaction.note().to_string())
            ),
        ]
    }
}

impl ProgramData {
    fn add_transaction(
        &mut self,
        date: Date,
        merchant_name_or_id: String,
        amount: Money,
        note: Option<String>,
    ) -> ShellReply {
        let merchant_id = match self.merchants.resolve_id(&merchant_name_or_id) {
            Ok(merchant_id) => merchant_id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        let transaction = match note {
            None => Transaction::new(date, merchant_id, amount),
            Some(note) => Transaction::new_with_note(date, merchant_id, amount, note),
        };
        let id = self.ledger.insert(transaction);
        ShellReply::ShortMessage(format!("Created new transaction with ID {}", id))
    }

    fn delete_transaction(&mut self, unparsed_id: String) -> ShellReply {
        let id = match self.ledger.resolve_id(&unparsed_id) {
            Ok(id) => id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        self.ledger
            .delete(id)
            .expect("resolved transaction id is valid");
        ShellReply::ShortMessage(format!("Transaction ID {} deleted", id))
    }

    fn recent_transactions(&self, how_many: Option<usize>) -> ShellReply {
        let count = match how_many {
            Some(count) => count,
            None => 10, // Default to showing the 10 most recent
        };
        let output = self.ledger
            .find_newest(count)
            .into_iter()
            .map(|transaction| {
                format!("{:?}", transaction)
            }).collect();
        ShellReply::LongMessage(output)
    }
}

impl ProgramData {
    fn display_merchant(&self, name_or_id: String) -> ShellReply {
        let id = match self.merchants.resolve_id(&name_or_id) {
            Ok(id) => id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        let full_name = self
            .merchants
            .get_full_name(id)
            .expect("resolved merchant id is valid");
        let nicknames = self
            .merchants
            .get_nicknames(id)
            .expect("resolved merchant id is valid");
        let mut output_lines = vec![
            format!("Merchant ID {}:", id),
            format!("    Full Name: {}", full_name),
            String::from("    Nicknames:"),
        ];
        let initial_length = output_lines.len();
        for nickname in nicknames {
            output_lines.push(format!("        {}", nickname));
        }
        if output_lines.len() == initial_length {
            // There were zero nicknames for this merchant
            output_lines.push(String::from("        (none)"))
        }
        ShellReply::LongMessage(output_lines)
    }

    fn establish_merchant(&mut self, full_name: String) -> ShellReply {
        match self.merchants.create(full_name) {
            Ok(id) => ShellReply::ShortMessage(format!("Created new merchant with ID {}", id)),
            Err(error) => ShellReply::ErrorMessage(Box::new(error)),
        }
    }

    fn demolish_merchant(&mut self, name_or_id: String) -> ShellReply {
        // TODO: Make sure this merchant is not used in any transactions first!!
        let id = match self.merchants.resolve_id(&name_or_id) {
            Ok(id) => id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        self.merchants
            .delete(id)
            .expect("resolved merchant id is valid");
        ShellReply::ShortMessage(format!("Merchant ID {} deleted", id))
    }

    fn renovate_merchant(&mut self, name_or_id: String, new_full_name: String) -> ShellReply {
        let id = match self.merchants.resolve_id(&name_or_id) {
            Ok(id) => id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        match self.merchants.rename(id, new_full_name) {
            Ok(_id) => ShellReply::ShortMessage(format!("Merchant ID {} renamed", id)),
            Err(error) => ShellReply::ErrorMessage(Box::new(error)),
        }
    }

    fn nickname_merchant(&mut self, name_or_id: String, nickname: String) -> ShellReply {
        let id = match self.merchants.resolve_id(&name_or_id) {
            Ok(id) => id,
            Err(error) => return ShellReply::ErrorMessage(Box::new(error)),
        };
        match self.merchants.nickname(id, nickname) {
            Ok(_id) => ShellReply::ShortMessage(format!("Nickname added to merchant ID {}", id)),
            Err(error) => ShellReply::ErrorMessage(Box::new(error)),
        }
    }

    fn de_nickname_merchant(&mut self, nickname: String) -> ShellReply {
        match self.merchants.de_nickname(&nickname) {
            Ok(id) => ShellReply::ShortMessage(format!("Nickname removed from merchant ID {}", id)),
            Err(error) => ShellReply::ErrorMessage(Box::new(error)),
        }
    }
}
