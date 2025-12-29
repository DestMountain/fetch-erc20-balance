import asyncio
import inspect
from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
except ImportError:
    from web3.middleware import geth_poa_middleware as poa_middleware
import json

# Base Sepolia archive RPC (required for historical state queries).
RPC_URL = "https://base-sepolia.gateway.tenderly.co"

# Replace with your wallet address (any case; will be checksummed)
YOUR_ADDRESS = "0xaa33a1a266821b7fb4e125c9d13fe300e3164c82"

# Token contract addresses (any case; will be checksummed)
TOKEN_ADDRESSES = [
    "0xf6b46c3c177d2256da671b8b51c88f26b40ff06e",  # hbfUSD (6 decimals)
    "0x25ffc79c6a796cfa42d4be6ffb44d603c66a341f",  # pbfUSD (6 decimals)
    # Add more as needed
]

# Multiple block heights to query
BLOCK_NUMBERS = [33900034, 33921869, 33983610, 34491707, 34494931, 34495497, 34579107]  # epoch 30-36

# Minimal ABI for decimals and balanceOf
DECIMALS_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]
BALANCE_OF_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]
TOTAL_SUPPLY_ABI = [
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

# Normalize to checksum to satisfy web3.py's strict address checks.
def normalize_address(address, label):
    try:
        return Web3.to_checksum_address(address)
    except ValueError as exc:
        raise ValueError(f"{label} address is invalid: {address}") from exc

# Support both sync and async web3 call styles across versions.
async def maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value

async def get_decimals(w3, token_address, block_number):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=DECIMALS_ABI)
        result = contract.functions.decimals().call(block_identifier=block_number)
        return await maybe_await(result)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_balance(w3, token_address, wallet_address, block_number):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=BALANCE_OF_ABI)
        result = contract.functions.balanceOf(wallet_address).call(block_identifier=block_number)
        return await maybe_await(result)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_total_supply(w3, token_address, block_number):
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=TOTAL_SUPPLY_ABI)
        result = contract.functions.totalSupply().call(block_identifier=block_number)
        return await maybe_await(result)
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    # Inject PoA middleware for Base (Optimism-based chain)
    w3.middleware_onion.inject(poa_middleware, layer=0)

    if not w3.is_connected():
        print("Cannot connect to Base Sepolia RPC. Please check your network or try another RPC endpoint.")
        return

    try:
        wallet_address = normalize_address(YOUR_ADDRESS, "Wallet")
    except ValueError as exc:
        print(str(exc))
        return

    token_addresses = []
    for token in TOKEN_ADDRESSES:
        try:
            token_addresses.append(normalize_address(token, "Token"))
        except ValueError as exc:
            print(str(exc))
            return

    print(f"Querying address: {wallet_address}")
    print(f"Block heights: {BLOCK_NUMBERS}")
    print(f"Number of tokens: {len(token_addresses)}\n")

    results = {}
    token_decimals = {}

    for token_idx, token in enumerate(token_addresses):
        results[token] = {}
        print(f"Processing token {token} ({token_idx + 1}/{len(token_addresses)})")

        # Fetch decimals using the first block (decimals are immutable)
        first_block = BLOCK_NUMBERS[0]
        decimals = await get_decimals(w3, token, first_block)
        if isinstance(decimals, str):  # Error occurred
            print(f"  Failed to fetch decimals: {decimals}")
            decimals = None
        else:
            print(f"  Decimals: {decimals}")

        token_decimals[token] = decimals

        for block_idx, block in enumerate(BLOCK_NUMBERS):
            print(f"  Querying balance at block {block}...")
            balance_raw = await get_balance(w3, token, wallet_address, block)
            print(f"  Querying total supply at block {block}...")
            total_supply_raw = await get_total_supply(w3, token, block)

            if decimals is not None and isinstance(balance_raw, int):
                balance_human = balance_raw / (10 ** decimals)
            else:
                balance_human = "N/A"

            if decimals is not None and isinstance(total_supply_raw, int):
                total_supply_human = total_supply_raw / (10 ** decimals)
            else:
                total_supply_human = "N/A"

            results[token][block] = {
                "balance_raw": balance_raw,
                "balance_human": balance_human,
                "total_supply_raw": total_supply_raw,
                "total_supply_human": total_supply_human
            }

            # Sleep to avoid rate limiting on public RPC
            await asyncio.sleep(0.3)

    # Print results
    print("\n=== Query Results ===")
    for token, block_data in results.items():
        decimals_used = token_decimals.get(token)
        decimals_used = decimals_used if decimals_used is not None else "unknown"
        print(f"\nToken: {token} (decimals: {decimals_used})")
        for block, data in block_data.items():
            print(f"  Block {block}:")
            print(f"    Balance Raw: {data['balance_raw']}")
            print(f"    Balance Human: {data['balance_human']}")
            print(f"    Total Supply Raw: {data['total_supply_raw']}")
            print(f"    Total Supply Human: {data['total_supply_human']}")

    # Save results to JSON file
    with open("balances_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print("\nResults have been saved to 'balances_result.json'")

# Run the async main function
asyncio.run(main())
