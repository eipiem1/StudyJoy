https://www.hackquest.io/learn/b99cca2c-679a-4241-ab30-f10069f5457e/19939e3f-d060-445b-b016-344f26e9a514

rustup default 1.81
rustup target add wasm32-unknown-unknown --toolchain 1.81

cargo stylus new <YOUR_PROJECT_NAME>

cargo stylus check -e https://sepolia-rollup.arbitrum.io/rpc
cargo stylus deploy -e $ARBITRUM_TESTNET_RPC --private-key=$PRIVATE_KEY --estimate-gas
cargo stylus deploy -e $ARBITRUM_TESTNET_RPC --private-key=$PRIVATE_KEY --estimate-gas --no-verify
cargo stylus deploy -e $ARBITRUM_TESTNET_RPC --private-key=$PRIVATE_KEY --no-verify

# Check
cast call --rpc-url $ARBITRUM_TESTNET_RPC $ARBITRUM_NFT_CA "balanceOf(address) (uint256)" $PUBLIC_ADDRESS
cast call --rpc-url $ARBITRUM_TESTNET_RPC $ARBITRUM_NFT_CA "ownerOf(uint256) (address)" 0

# Mint
cast send --rpc-url $ARBITRUM_TESTNET_RPC $ARBITRUM_NFT_CA --private-key $PRIVATE_KEY "safeMint(address)" $PUBLIC_ADDRESS

# Check again
cast call --rpc-url $ARBITRUM_TESTNET_RPC $ARBITRUM_NFT_CA "balanceOf(address) (uint256)" $PUBLIC_ADDRESS
cast call --rpc-url $ARBITRUM_TESTNET_RPC $ARBITRUM_NFT_CA "ownerOf(uint256) (address)" 0
