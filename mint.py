def _mint():
    import os
    from web3 import Web3

    RPC_URL = os.getenv("RPC_URL")
    ACCOUNT = os.getenv("PUBLIC_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")

    nftcontract_address = os.getenv("NFT_CONTRACT")
    receiver_address = os.getenv("NFT_RECEIVER")
    MINT_PRICE = os.getenv("NFT_MINT_PRICE")

    # Connect to an Ethereum node
    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    # Ensure you are connected
    if not w3.is_connected():
        raise Exception("Failed to connect to Ethereum node")

    with open("abi.json") as f:
        abi = f.read()

    # Create a contract instance
    contract_instance = w3.eth.contract(address=nftcontract_address, abi=abi)

    # Build the transaction
    tx = contract_instance.functions.mintTo(receiver_address).build_transaction({
        'nonce': w3.eth.get_transaction_count(ACCOUNT),
        'value': w3.to_wei(MINT_PRICE, 'ether')  # Specify the value (0.001 ether in this case)
    })

    # Sign the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

    # Send the transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the transaction to be mined
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return int.from_bytes(receipt.logs[0].topics[3], byteorder='big')

#contract_instance.functions.tokenURI().call(1)

