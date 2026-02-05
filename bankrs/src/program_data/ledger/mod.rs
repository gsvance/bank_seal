use std::cmp::Ordering;
use std::convert::From;
use std::error::Error;
use std::fmt::{self, Display};
use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::num::ParseIntError;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json;

mod comma_int;
mod date;
mod money;

use super::hex_id::{HexID, HexIDSpace};
pub use date::Date;
pub use money::Money;

#[derive(Debug, PartialEq)]
pub enum LedgerError {
    CantParseID(ParseIntError),
    UnusedID(HexID),
    EmptyDateRange,
    EmptyAmountRange,
}

impl Display for LedgerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::CantParseID(error) => write!(
                f, "{}", error
            ),
            Self::UnusedID(id) => write!(
                f, "no transaction currently exists with ID {}", id
            ),
            Self::EmptyDateRange => write!(
                f, "end of date range cannot come before start date"
            ),
            Self::EmptyAmountRange => write!(
                f, "upper end of amount range is greater than lower end"
            ),
        }
    }
}

impl Error for LedgerError {}

#[derive(Debug, Deserialize, Serialize)]
pub struct Transaction {
    date: Date,
    merchant_id: HexID,
    amount: Money,
    note: String,
}

impl Transaction {
    pub fn new(date: Date, merchant_id: HexID, amount: Money) -> Self {
        Self {
            date,
            merchant_id,
            amount,
            note: String::new(),
        }
    }

    pub fn new_with_note(date: Date, merchant_id: HexID, amount: Money, note: String) -> Self {
        Self {
            date,
            merchant_id,
            amount,
            note,
        }
    }

    pub fn date(&self) -> &Date {
        &self.date
    }

    pub fn merchant_id(&self) -> &HexID {
        &self.merchant_id
    }

    pub fn amount(&self) -> &Money {
        &self.amount
    }

    pub fn note(&self) -> &String {
        &self.note
    }
}

/*
impl Transaction {
    fn positive_amount(&self) -> Money {
        let zero = Money::new(0);
        if self.amount > zero {
            self.amount
        } else {
            zero
        }
    }

    fn negative_amount(&self) -> Money {
        let zero = Money::new(0);
        if self.amount < zero {
            self.amount
        } else {
            zero
        }
    }
}
*/

impl Transaction {
    fn erase_note(&mut self) {
        if self.note != "" {
            self.note = String::new();
        }
    }

    fn set_note(&mut self, note: String) {
        self.note = note;
    }
}

impl Ord for Transaction {
    fn cmp(&self, other: &Self) -> Ordering {
        match self.date.cmp(&other.date) {
            Ordering::Equal => {}
            unequal => return unequal,
        }
        match self.amount.cmp(&other.amount) {
            Ordering::Equal => {}
            Ordering::Greater => return Ordering::Less,
            Ordering::Less => return Ordering::Greater,
        }
        match self.merchant_id.cmp(&other.merchant_id) {
            Ordering::Equal => {}
            unequal => return unequal,
        }
        self.note.cmp(&other.note)
    }
}

impl PartialOrd for Transaction {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(&other))
    }
}

impl PartialEq for Transaction {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(&other) == Ordering::Equal
    }
}

impl Eq for Transaction {}

#[derive(Debug, PartialEq)]
pub struct LedgerRow {
    id: HexID,
    subtotal: Option<Money>,
}

impl LedgerRow {
    fn new(id: HexID) -> Self {
        Self {
            id,
            subtotal: None,
        }
    }

    pub fn id(&self) -> &HexID {
        &self.id
    }

    pub fn subtotal(&self) -> &Option<Money> {
        &self.subtotal
    }
}

#[derive(Debug, PartialEq)]
pub struct Ledger {
    space: HexIDSpace<Transaction>,
    rows: Vec<LedgerRow>,
}

impl Ledger {
    pub fn new() -> Self {
        Self {
            space: HexIDSpace::new(),
            rows: Vec::new(),
        }
    }
}

impl From<HexIDSpace<Transaction>> for Ledger {
    fn from(value: HexIDSpace<Transaction>) -> Self {
        let space = value;
        let mut rows = Vec::new();
        for id in space.ids() {
            rows.push(LedgerRow::new(id));
        }
        Self {
            space,
            rows,
        }
    }
}

impl Ledger {
    pub fn from_file(file_name: PathBuf) -> Result<Self, Box<dyn Error>> {
        let file = File::open(file_name)?;
        let reader = BufReader::new(file);
        let space: HexIDSpace<Transaction> = serde_json::from_reader(reader)?;
        Ok(Self::from(space))
    }

    pub fn to_file(&self, file_name: PathBuf) -> Result<(), Box<dyn Error>> {
        let file = File::create(file_name)?;
        let writer = BufWriter::new(file);
        Ok(serde_json::to_writer(writer, &self.space)?)
    }
}

impl Ledger {
    fn all_ids(&self) -> impl Iterator<Item = HexID> + '_ {
        self.space.ids()
    }

    fn n_ids(&self) -> usize {
        self.space.card()
    }
}

impl Ledger {
    fn organize(&mut self) {
        self.sort();
        self.do_subtotals();
    }

    fn sort(&mut self) {
        self.rows.sort_by_key(|row| {
            self.space.lookup(row.id)
                .expect("ids stored in self.rows should all be valid")
        });
    }

    fn do_subtotals(&mut self) {
        let mut subtotal = Money::new(0);
        for row in self.rows.iter_mut() {
            let transaction = self.space.lookup(row.id)
                .expect("ids stored in self.rows should all be valid");
            subtotal += transaction.amount;
            row.subtotal = Some(subtotal);
        }
    }
}

impl Ledger {
    pub fn resolve_id(&self, unparsed_id: &str) -> Result<HexID, LedgerError> {
        let id: HexID = match unparsed_id.parse() {
            Ok(id) => id,
            Err(error) => return Err(LedgerError::CantParseID(error)),
        };
        match self.space.lookup(id) {
            Some(_transaction) => Ok(id),
            None => Err(LedgerError::UnusedID(id)),
        }
    }
}

impl Ledger {
    pub fn insert(&mut self, transaction: Transaction) -> HexID {
        let id = self.space.deposit(transaction);
        self.rows.push(LedgerRow::new(id));
        self.organize();
        id
    }

    pub fn delete(&mut self, id: HexID) -> Result<HexID, LedgerError> {
        if let None = self.space.withdraw(id) {
            return Err(LedgerError::UnusedID(id));
        }
        self.rows.retain(|row| row.id != id);
        self.organize();
        Ok(id)
    }
}

impl Ledger {
    fn get_mut(&mut self, id: HexID) -> Result<&mut Transaction, LedgerError> {
        self.space.lookup_mut(id).ok_or(LedgerError::UnusedID(id))
    }

    pub fn update_date(
        &mut self,
        id: HexID,
        new_date: Date,
    ) -> Result<HexID, LedgerError> {
        self.get_mut(id)?.date = new_date;
        self.organize();
        Ok(id)
    }

    pub fn update_merchant_id(
        &mut self,
        id: HexID,
        new_merchant_id: HexID,
    ) -> Result<HexID, LedgerError> {
        self.get_mut(id)?.merchant_id = new_merchant_id;
        self.organize();
        Ok(id)
    }

    pub fn update_amount(
        &mut self,
        id: HexID,
        new_amount: Money,
    ) -> Result<HexID, LedgerError> {
        self.get_mut(id)?.amount = new_amount;
        self.organize();
        Ok(id)
    }

    pub fn update_note(
        &mut self,
        id: HexID,
        new_note: Option<String>,
    ) -> Result<HexID, LedgerError> {
        let transaction = self.get_mut(id)?;
        match new_note {
            Some(new_note) => transaction.note = new_note,
            None => transaction.erase_note(),
        }
        self.organize();
        Ok(id)
    }
}

impl Ledger {
    pub fn find_by_id(&self, id: HexID) -> Result<&Transaction, LedgerError> {
        match self.space.lookup(id) {
            Some(transaction) => Ok(transaction),
            None => Err(LedgerError::UnusedID(id)),
        }
    }

    pub fn find_newest(&self, count: usize) -> Vec<&Transaction> {
        self.rows.iter().rev().take(count).rev()
            .map(|row| {
                self.space.lookup(row.id)
                    .expect("ids stored in self.rows should always be valid")
            }).collect()
    }

    pub fn find_oldest(&self, count: usize) -> Vec<&Transaction> {
        self.rows.iter().take(count)
            .map(|row| {
                self.space.lookup(row.id)
                    .expect("ids stored in self.rows should always be valid")
            }).collect()
    }

    pub fn find_by_date(&self, date: Date) -> Vec<&Transaction> {
        self.find_in_date_range(date, date)
            .expect("date range with one date will not be empty")
    }

    pub fn find_in_date_range(
        &self,
        start_date: Date,
        end_date: Date,
    ) -> Result<Vec<&Transaction>, LedgerError> {
        if end_date < start_date {
            return Err(LedgerError::EmptyDateRange);
        }
        Ok(
            self.rows.iter()
            .map(|row| {
                self.space.lookup(row.id)
                    .expect("ids stored in self.rows should always be valid")
            }).filter(|transaction| {
                transaction.date >= start_date && transaction.date <= end_date
            }).collect()
        )
    }

    pub fn find_by_merchant_id(&self, merchant_id: HexID) -> Vec<&Transaction> {
        self.rows.iter()
            .map(|row| {
                self.space.lookup(row.id)
                    .expect("ids stored in self.rows should always be valid")
            }).filter(|transaction| {
                transaction.merchant_id == merchant_id
            }).collect()
    }

    pub fn find_by_amount(&self, amount: Money) -> Vec<&Transaction> {
        self.find_in_amount_range(amount, amount)
            .expect("amount range with one amount will not be empty")
    }

    pub fn find_in_amount_range(
        &self,
        lower_amount: Money,
        upper_amount: Money,
    ) -> Result<Vec<&Transaction>, LedgerError> {
        if upper_amount < lower_amount {
            return Err(LedgerError::EmptyAmountRange);
        }
        Ok(
            self.rows.iter()
            .map(|row| {
                self.space.lookup(row.id)
                    .expect("ids stored in self.rows should always be valid")
            }).filter(|transaction| {
                transaction.amount >= lower_amount && transaction.amount <= upper_amount
            }).collect()
        )
    }
}

#[cfg(test)]
mod test_ledger {
    use super::*;

    #[test]
    fn new() {
        let space: HexIDSpace<Transaction> = HexIDSpace::new();
        let rows: Vec<LedgerRow> = Vec::new();

        let ledger = Ledger::new();

        assert_eq!(ledger, Ledger { space, rows });
    }
}
