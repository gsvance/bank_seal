use std::collections::HashMap;
use std::fmt::{self, Debug, Display};
use std::num::ParseIntError;
use std::str::FromStr;

use rand;
use serde::{Deserialize, Serialize};

const HEX_BASE: u32 = 16;
const HEX_DIGIT_BITS: u32 = HEX_BASE.ilog2();

// Isolate the internal int type for HexID in case I want to change it
type HexInt = u32;

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Deserialize, Serialize)]
pub struct HexID(HexInt);

impl HexID {
    const BITS: u32 = HexInt::BITS;
    const DIGITS: u32 = Self::BITS.div_ceil(HEX_DIGIT_BITS);

    fn new<T: Into<HexInt>>(value: T) -> Self {
        Self(value.into())
    }

    fn random() -> Self {
        Self(rand::random())
    }

    const NUDGE: HexInt = 91; // Any number with no factors of 2

    fn nudge(self) -> Self {
        let next: HexInt = self.0.wrapping_add(Self::NUDGE);
        Self(next)
    }
}

impl Display for HexID {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut digits = ['_'; Self::DIGITS as usize];
        let mut value: HexInt = self.0;
        for digit in digits.iter_mut().rev() {
            let quotient: HexInt = value / HEX_BASE as HexInt;
            let remainder: u32 = (value % HEX_BASE as HexInt) as u32;
            *digit = char::from_digit(remainder, HEX_BASE)
                .expect("remainder will always be a valid hex digit");
            value = quotient;
        }
        write!(f, "{}", String::from_iter(digits))
    }
}

impl Debug for HexID {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "HexID(0x{})", self.to_string())
    }
}

impl FromStr for HexID {
    type Err = ParseIntError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let value = HexInt::from_str_radix(s, HEX_BASE)?;
        Ok(Self(value))
    }
}

#[cfg(test)]
mod test_hex_id {
    use super::*;

    #[test]
    fn new() {
        let value: u8 = 0xE1;

        let hexid = HexID::new(value);

        assert_eq!(hexid, HexID(0xE1));
    }

    #[test]
    fn nudge() {
        let hexid1 = HexID::random();

        let hexid2 = hexid1.nudge();

        assert_ne!(hexid1, hexid2);
    }

    #[test]
    fn display() {
        let value: HexInt = 0xAB43EF;
        let hexid = HexID::new(value);

        let string = format!("{}", hexid);

        assert_eq!(string, "00ab43ef");
    }

    #[test]
    fn debug() {
        let value: HexInt = 0x0E3D6C9B;
        let hexid = HexID::new(value);

        let string = format!("{:?}", hexid);

        assert_eq!(string, "HexID(0x0e3d6c9b)");
    }

    #[test]
    fn parse() {
        let value: HexInt = 0x0BEEF00D;
        let hexstr = "beef00d";
        let badstr = "123yab";

        let hexid1: Result<HexID, _> = hexstr.parse();
        let hexid2: Result<HexID, _> = badstr.parse();

        assert_eq!(hexid1, Ok(HexID::new(value)));
        assert!(hexid2.is_err());
    }
}

#[derive(Debug, PartialEq, Deserialize, Serialize)]
pub struct HexIDSpace<T>(HashMap<HexID, T>);

impl<T> HexIDSpace<T> {
    pub fn new() -> Self {
        Self(HashMap::new())
    }

    pub fn card(&self) -> usize {
        self.0.len()
    }

    fn generate_id(&self) -> HexID {
        if self.card() as u64 == HexInt::MAX as u64 {
            panic!("a hex id space has grown to maximum size");
        }
        let mut id = HexID::random();
        while self.0.contains_key(&id) {
            id = id.nudge();
        }
        id
    }
}

impl<T> HexIDSpace<T> {
    pub fn deposit(&mut self, value: T) -> HexID {
        let id = self.generate_id();
        self.0.insert(id, value);
        id
    }

    pub fn lookup(&self, id: HexID) -> Option<&T> {
        self.0.get(&id)
    }

    pub fn lookup_mut(&mut self, id: HexID) -> Option<&mut T> {
        self.0.get_mut(&id)
    }

    pub fn withdraw(&mut self, id: HexID) -> Option<T> {
        self.0.remove(&id)
    }
}

impl<T> HexIDSpace<T> {
    pub fn iter(&self) -> impl Iterator<Item = (HexID, &T)> {
        self.0.iter().map(|(&id, value)| (id, value))
    }

    pub fn ids(&self) -> impl Iterator<Item = HexID> + '_ {
        self.0.keys().map(|&id| id)
    }
}

#[cfg(test)]
mod test_hex_id_space {
    use super::*;

    #[test]
    fn new() {
        let map: HashMap<HexID, String> = HashMap::new();

        let space: HexIDSpace<String> = HexIDSpace::new();

        assert_eq!(space, HexIDSpace(map));
        assert_eq!(space.card(), 0);
    }

    #[test]
    fn deposit() {
        let mut space = HexIDSpace::new();
        let number = 20_000;

        for _ in 0..number {
            space.deposit(String::from("AbCdEfG"));
        }

        assert_eq!(space.card(), number);
    }

    #[test]
    fn lookup() {
        let mut space = HexIDSpace::new();
        let float = 2.75;
        let id = space.deposit(float);
        let bad = id.nudge();

        let look1 = space.lookup(id);
        let look2 = space.lookup(bad);

        assert_eq!(look1, Some(&float));
        assert_eq!(look2, None);
    }

    #[test]
    fn lookup_mut() {
        let mut space = HexIDSpace::new();
        let mut string = String::from("Bonjour");
        let id = space.deposit(string.clone());
        let bad = id.nudge();

        let ref1 = space.lookup_mut(id);

        assert_eq!(ref1, Some(&mut string));

        let ref2 = space.lookup_mut(bad);

        assert_eq!(ref2, None);

        let suffix = ", mon ami!";
        let mut mutated = string.clone();
        mutated.push_str(suffix);

        let ref3 = space.lookup_mut(id).unwrap();
        ref3.push_str(suffix);

        assert_eq!(space.lookup(id), Some(&mutated));
    }

    #[test]
    fn withdraw() {
        let mut space = HexIDSpace::new();
        let data = vec![1.0_f32, 2.0_f32];
        let id = space.deposit(data.clone());
        let bad = id.nudge();

        let result1 = space.withdraw(id);
        let result2 = space.withdraw(bad);
        let result3 = space.withdraw(id);

        assert_eq!(result1, Some(data));
        assert_eq!(result2, None);
        assert_eq!(result3, None);
        assert_eq!(space.card(), 0);
    }

    #[test]
    fn iter() {
        let mut space = HexIDSpace::new();
        let string1 = String::from("Alice");
        let string2 = String::from("Bob");
        let id1 = space.deposit(string1.clone());
        let id2 = space.deposit(string2.clone());
        let from_array = HashMap::from([(id1, &string1), (id2, &string2)]);

        let from_iter: HashMap<_, _> = space.iter().collect();

        assert_eq!(from_array, from_iter);
    }

    #[test]
    fn ids() {
        let mut space = HexIDSpace::new();
        let string1 = String::from("Splitsie");
        let string2 = String::from("Capac Amaru");
        let id1 = space.deposit(string1.clone());
        let id2 = space.deposit(string2.clone());
        let vec12 = vec![id1, id2];
        let vec21 = vec![id2, id1];

        let ids_vec: Vec<_> = space.ids().collect();

        assert!(ids_vec == vec12 || ids_vec == vec21);
    }
}
