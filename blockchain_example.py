"""
Example usage of the BlockchainService.

This script demonstrates various blockchain operations including
transaction monitoring, flash loan detection, and multi-chain support.
"""

import json
from blockchain_service import BlockchainService, FLASH_LOAN_SIGNATURES


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def main():
    """Run blockchain service examples."""
    
    # Example 1: Initialize and health check
    print_section("Example 1: Service Initialization")
    
    try:
        service = BlockchainService("ethereum")
        print(f"✓ Connected to {service.chain_name}")
        print(f"✓ RPC URL: {service.rpc_url}")
        print(f"✓ Health check: {service.health_check()}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nNote: This requires internet connection and working RPC endpoint")
        return
    
    # Example 2: Get latest block
    print_section("Example 2: Latest Block Information")
    
    block_info = service.get_latest_block()
    print(f"\nBlock Number: {block_info.block_number:,}")
    print(f"Timestamp: {block_info.timestamp}")
    print(f"Hash: {block_info.hash}")
    print(f"Transactions: {block_info.transaction_count}")
    print(f"Connected: {block_info.connected}")
    
    # Example 3: Flash loan signature detection
    print_section("Example 3: Flash Loan Signature Detection")
    
    print("\nKnown Flash Loan Signatures:")
    for protocol, signature in FLASH_LOAN_SIGNATURES.items():
        print(f"  • {protocol}: {signature}")
    
    # Test with example transactions
    test_transactions = [
        {
            'name': 'Aave Flash Loan',
            'input': '0x42b0b77c' + '0' * 100
        },
        {
            'name': 'dYdX Flash Loan',
            'input': '0x6bd3c1f3' + '0' * 100
        },
        {
            'name': 'Regular Transfer',
            'input': '0xa9059cbb' + '0' * 100
        }
    ]
    
    print("\nDetection Tests:")
    for tx in test_transactions:
        is_flash = service.is_flash_loan(tx)
        status = "✓ FLASH LOAN" if is_flash else "✗ Not flash loan"
        print(f"  {status} - {tx['name']}")
    
    # Example 4: Multi-chain support
    print_section("Example 4: Multi-Chain Support")
    
    chains = ["ethereum", "polygon", "arbitrum", "optimism"]
    
    for chain in chains:
        try:
            chain_service = BlockchainService(chain)
            block = chain_service.get_latest_block()
            print(f"\n{chain.upper()}:")
            print(f"  Block: {block.block_number:,}")
            print(f"  Connected: {block.connected}")
        except Exception as e:
            print(f"\n{chain.upper()}: ✗ {e}")
    
    # Example 5: Transaction details (with example hash)
    print_section("Example 5: Transaction Details")
    
    print("\nNote: Replace with actual transaction hash to test")
    print("Example format: 0x1234...abcd (66 characters)")
    
    # Example with invalid hash (will return None)
    example_hash = "0x" + "1234567890abcdef" * 4
    tx_details = service.get_transaction_details(example_hash)
    
    if tx_details:
        print(f"\nTransaction: {tx_details.hash}")
        print(f"From: {tx_details.from_address}")
        print(f"To: {tx_details.to_address}")
        print(f"Value: {tx_details.value}")
        print(f"Gas: {tx_details.gas}")
    else:
        print("\n✗ Transaction not found (expected for example hash)")
    
    # Example 6: Gas estimation
    print_section("Example 6: Gas Estimation")
    
    example_tx = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        'to': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'value': 0,
        'data': '0xa9059cbb'  # transfer function
    }
    
    print("\nEstimating gas for example transaction...")
    gas_estimate = service.estimate_gas(example_tx)
    
    if gas_estimate:
        print(f"✓ Estimated gas: {gas_estimate:,}")
    else:
        print("✗ Gas estimation failed (expected for example)")
    
    # Example 7: Block transaction scanning
    print_section("Example 7: Block Transaction Scanning")
    
    print("\nFetching transactions from latest block...")
    tx_hashes = service.get_block_transactions()
    
    print(f"Found {len(tx_hashes)} transactions")
    if tx_hashes:
        print(f"\nFirst 5 transactions:")
        for i, tx_hash in enumerate(tx_hashes[:5], 1):
            print(f"  {i}. {tx_hash}")
    
    # Example 8: Flash loan scanning
    print_section("Example 8: Flash Loan Scanning")
    
    print("\nScanning latest block for flash loans...")
    print("(This may take a while for blocks with many transactions)")
    
    flash_loans = service.scan_for_flash_loans()
    
    if flash_loans:
        print(f"\n✓ Found {len(flash_loans)} flash loan(s)!")
        for i, fl in enumerate(flash_loans, 1):
            print(f"\n  Flash Loan {i}:")
            print(f"    Hash: {fl['hash']}")
            print(f"    From: {fl['from']}")
            print(f"    To: {fl['to']}")
            print(f"    Value: {fl['value']}")
    else:
        print("\n✗ No flash loans found in latest block")
    
    # Example 9: Error handling
    print_section("Example 9: Error Handling")
    
    print("\nTesting with invalid inputs...")
    
    # Invalid transaction hash
    try:
        service.get_transaction_details("invalid_hash")
    except ValueError as e:
        print(f"✓ Caught invalid hash: {e}")
    
    # Invalid chain
    try:
        BlockchainService("invalid_chain")
    except ValueError as e:
        print(f"✓ Caught invalid chain: {e}")
    
    # Example 10: Custom RPC URL
    print_section("Example 10: Custom RPC URL")
    
    print("\nYou can use custom RPC URLs for better performance:")
    print("  • Infura: https://mainnet.infura.io/v3/YOUR_KEY")
    print("  • Alchemy: https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY")
    print("  • QuickNode: https://your-endpoint.quiknode.pro/YOUR_KEY")
    
    custom_service = BlockchainService(
        "ethereum",
        rpc_url="https://eth.llamarpc.com"  # Public endpoint
    )
    print(f"\n✓ Custom service initialized")
    print(f"  RPC: {custom_service.rpc_url}")
    
    # Summary
    print_section("Summary")
    print("\n✓ All examples completed!")
    print("\nKey Features Demonstrated:")
    print("  • Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism)")
    print("  • Latest block information retrieval")
    print("  • Transaction detail fetching")
    print("  • Flash loan signature detection")
    print("  • Gas estimation")
    print("  • Block transaction scanning")
    print("  • Automatic retry logic")
    print("  • Connection health monitoring")
    print("  • Error handling")
    print("\nThe blockchain service is ready for integration!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
