// Only run this as a WASM if the export-abi feature is not set.
#![cfg_attr(not(any(feature = "export-abi", test)), no_main)]
extern crate alloc;

use stylus_sdk::{msg, prelude::*};
mod erc721;
use crate::erc721::{Erc721, Erc721Error, Erc721Params, NotAuthorized};
use alloy_primitives::{Address, U256};

struct StylusNFTParams;

impl Erc721Params for StylusNFTParams {
    const NAME: &'static str = "StylusNFT";
    const SYMBOL: &'static str = "SNFT";
}

sol_storage! {
    #[entrypoint]
    struct StylusNFT {
        #[borrow]
        Erc721<StylusNFTParams> erc721;
        uint256 counter;
    }
}

#[public]
#[inherit(Erc721<StylusNFTParams>)]
impl StylusNFT {
    fn token_uri(token_id: U256) -> Result<String, Erc721Error> {
        Ok(format!("{}{}", "https://foobar/", token_id))
    }

    pub fn mint(&mut self, to: Address) -> Result<(), Erc721Error> {
        let token_id = self.counter.get();
        self.erc721._mint(to, token_id)?;

        let new_value = token_id + U256::from(1);
        self.counter.set(new_value);
        Ok(())
    }

    pub fn safe_mint(&mut self, to: Address) -> Result<(), Erc721Error> {
        let token_id = self.counter.get();
        self.erc721._safe_mint(to, token_id)?;

        let new_value = token_id + U256::from(1);
        self.counter.set(new_value);
        Ok(())
    }

    pub fn burn(&mut self, token_id: U256) -> Result<(), Erc721Error> {
        let owner = self.erc721._owners.get(token_id);
        if msg::sender() != owner {
            return Err(Erc721Error::NotAuthorized(NotAuthorized {
                caller: msg::sender(),
            }));
        };

        self.erc721._burn(token_id)?;
        Ok(())
    }
}
