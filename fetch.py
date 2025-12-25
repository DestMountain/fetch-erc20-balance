import asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json

# Base Sepolia public RPC
RPC_URL = "https://sepolia.base.org"

# Replace with your wallet address (lowercase)
YOUR_ADDRESS = "0xYourWalletAddressHere".lower()

# Token contract addresses
TOKEN_ADDRESSES = [
    "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # Example: Testnet USDC (6 decimals)
    # "0xAnotherTokenAddress",
    # Add more as needed
]

# Multiple block heights to query
BLOCK_NUMBERS = [5000000, 5500000, 6000000, 6500000]  # Replace with your desired blocks

# Minimal ABI for decimals and balanceOf
DECIMALS_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]
BALANCE_OF_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

async def get_decimals(w3, token_address, block_number):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=DECIMALS_ABI)
        return await contract.functions.decimals().call(block_identifier=block_number)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_balance(w3, token_address, block_number):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=BALANCE_OF_ABI)
        return await contract.functions.balanceOf(YOUR_ADDRESS).call(block_identifier=block_number)
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    # Inject PoA middleware for Base (Optimism-based chain)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.is_connected():
        print("Cannot connect to Base Sepolia RPC. Please check your network or try another RPC endpoint.")
        return

    print(f"Querying address: {YOUR_ADDRESS}")
    print(f"Block heights: {BLOCK_NUMBERS}")
    print(f"Number of tokens: {len(TOKEN_ADDRESSES)}\n")

    results = {}

    for token_idx, token in enumerate(TOKEN_ADDRESSES):
        results[token] = {}
        print(f"Processing token {token} ({token_idx + 1}/{len(TOKEN_ADDRESSES)})")

        # Fetch decimals using the first block (decimals are immutable)
        first_block = BLOCK_NUMBERS[0]
        decimals = await get_decimals(w3, token, first_block)
        if isinstance(decimals, str):  # Error occurred
            print(f"  Failed to fetch decimals: {decimals}")
            decimals = None
        else:
            print(f"  Decimals: {decimals}")

        for block_idx, block in enumerate(BLOCK_NUMBERS):
            print(f"  Querying balance at block {block}...")
            balance_raw = await get_balance(w3, token, block)

            if decimals is not None and isinstance(balance_raw, int):
                balance_human = balance_raw / (10 ** decimals)
            else:
                balance_human = "N/A"

            results[token][block] = {
                "raw": balance_raw,
                "human": balance_human
            }

            # Sleep to avoid rate limiting on public RPC
            await asyncio.sleep(0.3)

    # Print results
    print("\n=== Query Results ===")
    for token, block_data in results.items():
        decimals_used = decimals if decimals is not None else "unknown"
        print(f"\nToken: {token} (decimals: {decimals_used})")
        for block, data in block_data.items():
            print(f"  Block {block}:")
            print(f"    Raw Amount: {data['raw']}")
            print(f"    Human-readable Amount: {data['human']}")

    # Save results to JSON file
    with open("balances_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print("\nResults have been saved to 'balances_result.json'")

# Run the async main function
asyncio.run(main())