use std::collections::HashMap;
use std::error::Error;
use std::fmt::{self, Display};
use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json;

use super::hex_id::{HexID, HexIDSpace};

#[derive(Debug)]
pub enum MerchantError {
    CannotResolveID,
    ReadingWithBadID,
    NameAlreadyInUse,
    NameNotANickname,
    MutatingWithBadID,
    NameDoesNotExist,
}

impl Display for MerchantError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::CannotResolveID => write!(f, "failed to resolve input to any valid merchant ID"),
            Self::ReadingWithBadID => {
                write!(f, "cannot read a merchant without a valid merchant ID")
            }
            Self::NameAlreadyInUse => write!(f, "name is already in use by an existing merchant"),
            Self::NameNotANickname => {
                write!(f, "name is being used as a full name, not as a nickname")
            }
            Self::MutatingWithBadID => {
                write!(f, "cannot mutate a merchant without a valid merchant ID")
            }
            Self::NameDoesNotExist => write!(f, "name does not refer to any existing merchant"),
        }
    }
}

impl Error for MerchantError {}

#[derive(Debug, Deserialize, Serialize)]
pub struct Merchant {
    full_name: String,
    nicknames: Vec<String>,
}

impl Merchant {
    pub fn full_name(&self) -> &String {
        &self.full_name
    }

    pub fn nicknames(&self) -> &Vec<String> {
        &self.nicknames
    }
}

impl PartialEq for Merchant {
    fn eq(&self, other: &Self) -> bool {
        if self.full_name != other.full_name {
            return false;
        }
        for nickname in self.nicknames.iter() {
            if !other.nicknames.contains(nickname) {
                return false;
            }
        }
        for nickname in other.nicknames.iter() {
            if !self.nicknames.contains(nickname) {
                return false;
            }
        }
        true
    }
}

#[derive(Debug, PartialEq)]
pub struct Merchants {
    space: HexIDSpace<Merchant>,
    names: HashMap<String, HexID>,
}

impl Merchants {
    pub fn new() -> Self {
        Self {
            space: HexIDSpace::new(),
            names: HashMap::new(),
        }
    }
}

impl From<HexIDSpace<Merchant>> for Merchants {
    fn from(value: HexIDSpace<Merchant>) -> Self {
        let space = value;
        let mut names = HashMap::new();
        for (id, merchant) in space.iter() {
            names.insert(merchant.full_name.clone(), id);
            for nickname in merchant.nicknames.iter() {
                names.insert(nickname.clone(), id);
            }
        }
        Self { space, names }
    }
}

impl Merchants {
    pub fn from_file(file_name: PathBuf) -> Result<Self, Box<dyn Error>> {
        let file = File::open(file_name)?;
        let reader = BufReader::new(file);
        let space: HexIDSpace<Merchant> = serde_json::from_reader(reader)?;
        Ok(Self::from(space))
    }

    pub fn to_file(&self, file_name: PathBuf) -> Result<(), Box<dyn Error>> {
        let file = File::create(file_name)?;
        let writer = BufWriter::new(file);
        Ok(serde_json::to_writer(writer, &self.space)?)
    }
}

/*
impl Merchants {
    fn all_names(&self) -> impl Iterator<Item = &str> {
        self.names.keys().map(|name| name as &str)
    }

    fn all_ids(&self) -> impl Iterator<Item = HexID> + '_ {
        self.space.ids()
    }

    fn n_names(&self) -> usize {
        self.names.len()
    }

    fn n_ids(&self) -> usize {
        self.space.card()
    }

    fn n_full_names(&self) -> usize {
        self.n_ids()
    }

    fn n_nicknames(&self) -> usize {
        self.n_names() - self.n_full_names()
    }
}
*/

impl Merchants {
    fn get_id(&self, name: &str) -> Option<HexID> {
        self.names.get(name).map(|&id| id)
    }

    pub fn resolve_id(&self, name_or_id: &str) -> Result<HexID, MerchantError> {
        // First, try interpreting name_or_id as a merchant name
        if let Some(id) = self.get_id(name_or_id) {
            return Ok(id);
        }

        // If that fails, then try to parse name_or_id as a hex id
        if let Ok(id) = name_or_id.parse::<HexID>() {
            if let Some(_merchant) = self.space.lookup(id) {
                return Ok(id);
            }
        }

        // At this point, name_or_id is not recognized as either thing
        Err(MerchantError::CannotResolveID)
    }
}

impl Merchants {
    pub fn get_full_name(&self, id: HexID) -> Result<&str, MerchantError> {
        match self.space.lookup(id) {
            Some(merchant) => Ok(&merchant.full_name),
            None => Err(MerchantError::ReadingWithBadID),
        }
    }

    pub fn get_nicknames(&self, id: HexID) -> Result<impl Iterator<Item = &str>, MerchantError> {
        match self.space.lookup(id) {
            Some(merchant) => Ok(merchant.nicknames.iter().map(|nickname| nickname as &str)),
            None => Err(MerchantError::ReadingWithBadID),
        }
    }
}

impl Merchants {
    pub fn create(&mut self, full_name: String) -> Result<HexID, MerchantError> {
        if self.names.contains_key(&full_name) {
            return Err(MerchantError::NameAlreadyInUse);
        }
        let merchant = Merchant {
            full_name: full_name.clone(),
            nicknames: Vec::new(),
        };
        let id = self.space.deposit(merchant);
        self.names.insert(full_name, id);
        Ok(id)
    }

    pub fn nickname(&mut self, id: HexID, nickname: String) -> Result<HexID, MerchantError> {
        if self.names.contains_key(&nickname) {
            return Err(MerchantError::NameAlreadyInUse);
        }
        match self.space.lookup_mut(id) {
            None => Err(MerchantError::MutatingWithBadID),
            Some(merchant) => {
                merchant.nicknames.push(nickname.clone());
                self.names.insert(nickname, id);
                Ok(id)
            }
        }
    }

    pub fn de_nickname(&mut self, nickname: &str) -> Result<HexID, MerchantError> {
        let id = match self.get_id(nickname) {
            Some(id) => id,
            None => return Err(MerchantError::NameDoesNotExist),
        };
        let merchant = self
            .space
            .lookup_mut(id)
            .expect("the id we just fetched should still be valid");
        if nickname == merchant.full_name {
            return Err(MerchantError::NameNotANickname);
        }
        self.names.remove(nickname);
        merchant.nicknames.retain(|nn| nn != nickname);
        Ok(id)
    }

    pub fn delete(&mut self, id: HexID) -> Result<HexID, MerchantError> {
        let merchant = match self.space.lookup(id) {
            Some(merchant) => merchant,
            None => return Err(MerchantError::MutatingWithBadID),
        };
        for nickname in merchant.nicknames.iter() {
            self.names.remove(nickname);
        }
        self.names.remove(&merchant.full_name);
        self.space.withdraw(id);
        Ok(id)
    }

    pub fn rename(&mut self, id: HexID, new_full_name: String) -> Result<HexID, MerchantError> {
        let merchant = match self.space.lookup_mut(id) {
            Some(merchant) => merchant,
            None => return Err(MerchantError::MutatingWithBadID),
        };
        let old_full_name = &merchant.full_name;
        self.names.remove(old_full_name);
        self.names.insert(new_full_name.clone(), id);
        merchant.full_name = new_full_name;
        Ok(id)
    }
}

#[cfg(test)]
mod test_merchants {
    use super::*;

    #[test]
    fn new() {
        let space: HexIDSpace<Merchant> = HexIDSpace::new();
        let names: HashMap<String, HexID> = HashMap::new();

        let merchants = Merchants::new();

        assert_eq!(merchants, Merchants { space, names });
    }
}
