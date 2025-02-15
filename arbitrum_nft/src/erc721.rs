use core::marker::PhantomData;
use stylus_sdk::{
    alloy_primitives::{Address, U256},
    alloy_sol_types::sol,
    call::Call,
    msg,
    prelude::*,
};

pub trait Erc721Params {
    const NAME: &'static str;
    const SYMBOL: &'static str;
}

sol_storage! {
    pub struct Erc721<T> {
        mapping(uint256 => address) _owners;
        mapping(address => uint256) _balances;
        mapping(uint256 => address) _approvals;
        mapping(address => mapping(address => bool)) _approvals_for_all;
        PhantomData<T> phantom;
    }
}

sol! {
    event Transfer(address indexed from, address indexed to, uint256 indexed token_id);
    event Approval(address indexed owner, address indexed spender, uint256 indexed token_id);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    error NotOwner(address account, uint256 token_id);
    error NotAuthorized(address caller);
    error InvalidRecipient(address to);
    error AlreadyMinted(uint256 token_id);
    error NotMinted(uint256 token_id);
    error UnsafeRecipient(address recipient);
    error CallFailed();
}

sol! {
    interface IERC721TokenReceiver {
        function onERC721Received(address operator, address from, uint256 token_id, bytes calldata data) external returns(bytes4);
    }
}

#[derive(SolidityError)]
pub enum Erc721Error {
    NotOwner(NotOwner),
    NotAuthorized(NotAuthorized),
    InvalidRecipient(InvalidRecipient),
    AlreadyMinted(AlreadyMinted),
    NotMinted(NotMinted),
    UnsafeRecipient(UnsafeRecipient),
    CallFailed(CallFailed),
}

#[public]
impl<T: Erc721Params> Erc721<T> {
    pub fn _mint(&mut self, to: Address, token_id: U256) -> Result<(), Erc721Error> {
        if to.is_zero() {
            return Err(Erc721Error::InvalidRecipient(InvalidRecipient { to }));
        }

        if self._owners.get(token_id) != Address::ZERO {
            return Err(Erc721Error::AlreadyMinted(AlreadyMinted { token_id }));
        }

        self._balances.insert(to, self._balances.get(to) + U256::from(1));
        self._owners.insert(token_id, to);
        
        Ok(())
    }

    pub fn _safe_mint(&mut self, to: Address, token_id: U256) -> Result<(), Erc721Error> {
        self._mint(to, token_id)?;

        if stylus_sdk::contract::is_contract(to) {
            let data = Vec::new();
            let selector = IERC721TokenReceiver::onERC721ReceivedCall::SELECTOR;
            let result = Call::new()
                .call_selector(selector)
                .dest(to)
                .args((msg::sender(), Address::ZERO, token_id, data))
                .call()
                .map_err(|_| Erc721Error::CallFailed(CallFailed {}))?;

            if !result.as_slice().starts_with(&selector) {
                return Err(Erc721Error::UnsafeRecipient(UnsafeRecipient { recipient: to }));
            }
        }

        Ok(())
    }

    pub fn _burn(&mut self, token_id: U256) -> Result<(), Erc721Error> {
        let owner = self._owners.get(token_id);
        if owner == Address::ZERO {
            return Err(Erc721Error::NotMinted(NotMinted { token_id }));
        }

        self._balances.insert(owner, self._balances.get(owner) - U256::from(1));
        self._owners.insert(token_id, Address::ZERO);
        
        Ok(())
    }
}
