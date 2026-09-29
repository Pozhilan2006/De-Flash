"""
Web3 Blockchain Integration Service for Flash Loan Monitoring

This module provides a comprehensive blockchain service for interacting with
Ethereum-compatible chains. It includes transaction monitoring, flash loan
detection, and connection health management.

Author: DeFi Flash Loan Security Team
Version: 1.0.0
"""

import logging
import time
from typing import Dict, Optional, Any, List
from enum import Enum

try:
    from web3 import Web3
    from web3.exceptions import TransactionNotFound, BlockNotFound
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logging.warning("Web3.py not available. Install with: pip install web3")

from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChainConfig(str, Enum):
    """Supported blockchain networks with default RPC endpoints."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


# Default RPC endpoints (public, rate-limited)
DEFAULT_RPC_URLS = {
    ChainConfig.ETHEREUM: "https://eth.llamarpc.com",
    ChainConfig.POLYGON: "https://polygon-rpc.com",
    ChainConfig.ARBITRUM: "https://arb1.arbitrum.io/rpc",
    ChainConfig.OPTIMISM: "https://mainnet.optimism.io"
}

# Flash loan function signatures
FLASH_LOAN_SIGNATURES = {
    "aave_flashloan": "0x42b0b77c",
    "aave_flashloan_simple": "0xab9c4b5d",
    "dydx_flashloan": "0x6bd3c1f3",
    "uniswap_flashswap": "0xafa4d3b0",
    "uniswap_v3_flash": "0x490e6cbc",
    "balancer_flashloan": "0x5c38449e",
}


class BlockInfo(BaseModel):
    """Block information model."""
    block_number: int
    timestamp: int
    connected: bool
    hash: Optional[str] = None
    transaction_count: Optional[int] = None


class TransactionDetails(BaseModel):
    """Transaction details model."""
    hash: str
    from_address: str = Field(alias="from")
    to_address: Optional[str] = Field(alias="to")
    value: int
    gas: int
    gas_price: int
    input: str
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    transaction_index: Optional[int] = None
    nonce: Optional[int] = None
    
    class Config:
        populate_by_name = True


class BlockchainService:
    """
    Web3 blockchain service for Ethereum-compatible chains.
    
    This service provides methods for interacting with blockchain networks,
    including transaction monitoring, flash loan detection, and gas estimation.
    It includes automatic retry logic and connection health monitoring.
    """
    
    def __init__(
        self,
        chain_name: str,
        rpc_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the blockchain service.
        
        Args:
            chain_name: Name of the blockchain (ethereum, polygon, arbitrum, optimism)
            rpc_url: Custom RPC URL (uses default if not provided)
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
            
        Raises:
            ValueError: If Web3.py is not installed or chain is not supported
            ConnectionError: If initial connection fails
        """
        if not WEB3_AVAILABLE:
            raise ValueError(
                "Web3.py is required. Install with: pip install web3"
            )
        
        self.chain_name = chain_name.lower()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Get RPC URL
        if rpc_url:
            self.rpc_url = rpc_url
        else:
            try:
                chain_enum = ChainConfig(self.chain_name)
                self.rpc_url = DEFAULT_RPC_URLS[chain_enum]
            except ValueError:
                raise ValueError(
                    f"Unsupported chain: {chain_name}. "
                    f"Supported: {[c.value for c in ChainConfig]}"
                )
        
        logger.info(f"Initializing BlockchainService for {self.chain_name}")
        logger.info(f"RPC URL: {self.rpc_url}")
        
        # Initialize Web3
        self.w3: Optional[Web3] = None
        self._connect()
        
        # Verify connection
        if not self.health_check():
            raise ConnectionError(
                f"Failed to connect to {self.chain_name} at {self.rpc_url}"
            )
        
        logger.info(f"Successfully connected to {self.chain_name}")
    
    def _connect(self) -> None:
        """Establish Web3 connection."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            logger.debug(f"Web3 provider initialized for {self.chain_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Web3 provider: {e}")
            raise
    
    def _retry_on_failure(self, func, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    # Try to reconnect
                    try:
                        self._connect()
                    except Exception as reconnect_error:
                        logger.error(f"Reconnection failed: {reconnect_error}")
        
        logger.error(f"All {self.max_retries} attempts failed")
        raise last_exception
    
    def health_check(self) -> bool:
        """
        Check connection health.
        
        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            if self.w3 is None:
                return False
            
            # Try to get latest block number
            self.w3.eth.block_number
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_latest_block(self) -> BlockInfo:
        """
        Get latest block information.
        
        Returns:
            BlockInfo with block number, timestamp, and connection status
            
        Raises:
            Exception: If request fails after all retries
        """
        logger.info("Fetching latest block information")
        
        def _fetch_block():
            block = self.w3.eth.get_block('latest')
            return BlockInfo(
                block_number=block['number'],
                timestamp=block['timestamp'],
                connected=True,
                hash=block['hash'].hex(),
                transaction_count=len(block['transactions'])
            )
        
        try:
            return self._retry_on_failure(_fetch_block)
        except Exception as e:
            logger.error(f"Failed to fetch latest block: {e}")
            # Return disconnected state
            return BlockInfo(
                block_number=0,
                timestamp=0,
                connected=False
            )
    
    def get_transaction_details(self, tx_hash: str) -> Optional[TransactionDetails]:
        """
        Get detailed information about a transaction.
        
        Args:
            tx_hash: Transaction hash (with or without 0x prefix)
            
        Returns:
            TransactionDetails or None if transaction not found
            
        Raises:
            ValueError: If tx_hash format is invalid
        """
        # Normalize hash
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        if len(tx_hash) != 66:
            raise ValueError(f"Invalid transaction hash length: {tx_hash}")
        
        logger.info(f"Fetching transaction details for {tx_hash}")
        
        def _fetch_transaction():
            try:
                tx = self.w3.eth.get_transaction(tx_hash)
                
                return TransactionDetails(
                    hash=tx['hash'].hex(),
                    from_address=tx['from'],
                    to_address=tx.get('to'),
                    value=tx['value'],
                    gas=tx['gas'],
                    gas_price=tx['gasPrice'],
                    input=tx['input'].hex() if isinstance(tx['input'], bytes) else tx['input'],
                    block_number=tx.get('blockNumber'),
                    block_hash=tx.get('blockHash').hex() if tx.get('blockHash') else None,
                    transaction_index=tx.get('transactionIndex'),
                    nonce=tx.get('nonce')
                )
            except TransactionNotFound:
                logger.warning(f"Transaction not found: {tx_hash}")
                return None
        
        try:
            return self._retry_on_failure(_fetch_transaction)
        except Exception as e:
            logger.error(f"Failed to fetch transaction: {e}")
            return None
    
    def is_flash_loan(self, tx_data: Dict[str, Any]) -> bool:
        """
        Detect if transaction is a flash loan based on function signature.
        
        Args:
            tx_data: Transaction data dictionary (must contain 'input' field)
            
        Returns:
            True if flash loan signature detected, False otherwise
        """
        try:
            input_data = tx_data.get('input', '')
            
            # Normalize input data
            if isinstance(input_data, bytes):
                input_data = input_data.hex()
            
            if not input_data.startswith('0x'):
                input_data = '0x' + input_data
            
            # Extract function signature (first 4 bytes = 8 hex chars + 0x)
            if len(input_data) < 10:
                return False
            
            signature = input_data[:10].lower()
            
            # Check against known flash loan signatures
            is_flash = signature in FLASH_LOAN_SIGNATURES.values()
            
            if is_flash:
                # Find which protocol
                protocol = next(
                    (k for k, v in FLASH_LOAN_SIGNATURES.items() if v == signature),
                    "unknown"
                )
                logger.info(f"Flash loan detected: {protocol} ({signature})")
            
            return is_flash
            
        except Exception as e:
            logger.error(f"Error detecting flash loan: {e}")
            return False
    
    def estimate_gas(self, tx_data: Dict[str, Any]) -> Optional[int]:
        """
        Estimate gas required for a transaction.
        
        Args:
            tx_data: Transaction data dictionary with 'from', 'to', 'data', etc.
            
        Returns:
            Estimated gas amount or None if estimation fails
        """
        logger.info("Estimating gas for transaction")
        
        def _estimate():
            try:
                # Build transaction dict
                transaction = {
                    'from': tx_data.get('from'),
                    'to': tx_data.get('to'),
                }
                
                if 'value' in tx_data:
                    transaction['value'] = tx_data['value']
                
                if 'data' in tx_data or 'input' in tx_data:
                    transaction['data'] = tx_data.get('data') or tx_data.get('input')
                
                # Estimate gas
                gas_estimate = self.w3.eth.estimate_gas(transaction)
                logger.info(f"Gas estimate: {gas_estimate}")
                return gas_estimate
                
            except Exception as e:
                logger.error(f"Gas estimation failed: {e}")
                return None
        
        try:
            return self._retry_on_failure(_estimate)
        except Exception:
            return None
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt (for confirmed transactions).
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Receipt dictionary or None if not found
        """
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        logger.info(f"Fetching receipt for {tx_hash}")
        
        def _fetch_receipt():
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                return dict(receipt)
            except TransactionNotFound:
                logger.warning(f"Receipt not found: {tx_hash}")
                return None
        
        try:
            return self._retry_on_failure(_fetch_receipt)
        except Exception as e:
            logger.error(f"Failed to fetch receipt: {e}")
            return None
    
    def get_block_transactions(
        self,
        block_number: Optional[int] = None
    ) -> List[str]:
        """
        Get all transaction hashes in a block.
        
        Args:
            block_number: Block number (uses latest if None)
            
        Returns:
            List of transaction hashes
        """
        block_id = block_number if block_number is not None else 'latest'
        logger.info(f"Fetching transactions from block {block_id}")
        
        def _fetch_transactions():
            try:
                block = self.w3.eth.get_block(block_id, full_transactions=False)
                return [tx.hex() for tx in block['transactions']]
            except BlockNotFound:
                logger.warning(f"Block not found: {block_id}")
                return []
        
        try:
            return self._retry_on_failure(_fetch_transactions)
        except Exception as e:
            logger.error(f"Failed to fetch block transactions: {e}")
            return []
    
    def scan_for_flash_loans(
        self,
        block_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan a block for flash loan transactions.
        
        Args:
            block_number: Block number to scan (uses latest if None)
            
        Returns:
            List of flash loan transactions with details
        """
        logger.info(f"Scanning block {block_number or 'latest'} for flash loans")
        
        flash_loans = []
        tx_hashes = self.get_block_transactions(block_number)
        
        for tx_hash in tx_hashes:
            tx_details = self.get_transaction_details(tx_hash)
            
            if tx_details and self.is_flash_loan(tx_details.model_dump()):
                flash_loans.append({
                    'hash': tx_hash,
                    'from': tx_details.from_address,
                    'to': tx_details.to_address,
                    'value': tx_details.value,
                    'block_number': tx_details.block_number
                })
        
        logger.info(f"Found {len(flash_loans)} flash loan(s) in block")
        return flash_loans


# Example usage
if __name__ == "__main__":
    # Initialize service for Ethereum
    service = BlockchainService("ethereum")
    
    # Get latest block
    block_info = service.get_latest_block()
    print("\n=== Latest Block ===")
    print(f"Block Number: {block_info.block_number}")
    print(f"Timestamp: {block_info.timestamp}")
    print(f"Connected: {block_info.connected}")
    print(f"Transactions: {block_info.transaction_count}")
    
    # Health check
    print("\n=== Health Check ===")
    print(f"Service healthy: {service.health_check()}")
    
    # Example transaction (replace with actual hash)
    print("\n=== Transaction Detection ===")
    print("Note: Use actual transaction hash to test detection")
    
    # Example flash loan detection
    example_tx = {
        'input': '0x42b0b77c' + '0' * 100  # Aave flash loan signature
    }
    is_flash = service.is_flash_loan(example_tx)
    print(f"Is flash loan: {is_flash}")
