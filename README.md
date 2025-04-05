# Overview
A simple gamified language learning app featuring AI & web3. LLM/VLM are used to generate podcasts and flashcards, web3 is used for login, minting certifacte NFTs, and issuing community ERC20 tokens.

### Tech used
- Python and Flask for backend and routing 
- HTML, CSS, Javascript and Jinja for frontend 
- SQLite for storing data in databases

### Usage Instructions
- All required dependencies to run the app are in 'requirements.txt'
- Use `flask run` to run the app from the root directory

### Test
- Blockchains: Tested on Mantle, Arbitrum, Flow test networks
- LLM: Tested on deepseekV3/Qwen2.5
- VLM: Tested on Flux

### Enviornment
```
export RPC_URL=
export PUBLIC_ADDRESS=
export PRIVATE_KEY=
export NFT_CONTRACT=
export NFT_RECEIVER=
export NFT_MINT_PRICE=0.001

export OPENAI_API_BASE="https://api.siliconflow.cn/v1"
export OPENAI_API_KEY=
export OPENAI_API_MODEL="Qwen/Qwen2.5-7B-Instruct"
export OPENAI_API_VLM_MODEL="black-forest-labs/FLUX.1-schnell"
```

### Blockchain testnet RPC
- Mantle: https://rpc.testnet.mantle.xyz
- Arbitrum: https://sepolia-rollup.arbitrum.io/rpc
- Flow: https://testnet.evm.nodes.onflow.org/
- local: 127.0.0.1:8545

### Blockchain testnet browser
- Mantle: https://sepolia.mantlescan.xyz/
- Arbitrum: https://sepolia.arbiscan.io/
- Flow: https://evm-testnet.flowscan.io/

### Acknowledgements
