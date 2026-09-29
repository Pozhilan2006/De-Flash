"""
Rule-Based Risk Assessment Engine for Flash Loan Security

This module provides a configurable rule-based risk assessment system
for flash loan transactions. It supports chain-specific rules, token
blacklists, protocol risk scores, and transaction pattern detection.

Author: DeFi Flash Loan Security Team
Version: 1.0.0
"""

import logging
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Chain(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"
    AVALANCHE = "avalanche"


class TransactionType(str, Enum):
    """Categorized transaction types for pattern detection."""
    SWAP = "swap"
    BORROW = "borrow"
    LEND = "lend"
    LIQUIDATION = "liquidation"
    ARBITRAGE = "arbitrage"
    FLASH_LOAN = "flash_loan"
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    UNKNOWN = "unknown"


class AssessmentRequest(BaseModel):
    """
    Request model for risk assessment.
    
    Attributes:
        loan_amount: Amount of the flash loan in USD
        token: Token contract address
        protocol: Protocol name (e.g., 'aave', 'compound')
        transaction_type: Type of transaction
        chain: Blockchain network
        transaction_count: Number of recent transactions
    """
    loan_amount: float = Field(gt=0, description="Loan amount in USD")
    token: str = Field(min_length=1, description="Token contract address")
    protocol: str = Field(min_length=1, description="Protocol name")
    transaction_type: TransactionType = Field(description="Transaction type")
    chain: Chain = Field(description="Blockchain network")
    transaction_count: int = Field(ge=0, description="Recent transaction count")

    @field_validator('token')
    @classmethod
    def validate_token_address(cls, v: str) -> str:
        """Validate token address format."""
        if v.startswith('0x') and len(v) == 42:
            return v.lower()
        # Allow non-Ethereum addresses or token symbols for flexibility
        return v.lower()


class RuleCheckResult(BaseModel):
    """Result of a single rule check."""
    passed: bool
    penalty: int = Field(ge=0)
    message: Optional[str] = None


class AssessmentResponse(BaseModel):
    """
    Response model for risk assessment.
    
    Attributes:
        score: Overall risk score (0-100)
        violations: List of violated rule names
        details: Detailed results for each rule check
        risk_level: Categorized risk level
    """
    score: int = Field(ge=0, le=100)
    violations: List[str]
    details: Dict[str, RuleCheckResult]
    risk_level: str


class RuleEngine:
    """
    Rule-based risk assessment engine for flash loan security.
    
    This engine evaluates transactions against configurable rules including
    loan amount limits, token blacklists, protocol risk scores, and
    suspicious transaction patterns.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "chains": {
            "ethereum": {
                "max_loan_amount": 5_000_000,
                "max_transaction_count": 1000
            },
            "polygon": {
                "max_loan_amount": 1_000_000,
                "max_transaction_count": 2000
            },
            "arbitrum": {
                "max_loan_amount": 2_000_000,
                "max_transaction_count": 1500
            },
            "optimism": {
                "max_loan_amount": 2_000_000,
                "max_transaction_count": 1500
            },
            "bsc": {
                "max_loan_amount": 1_500_000,
                "max_transaction_count": 2000
            },
            "avalanche": {
                "max_loan_amount": 1_500_000,
                "max_transaction_count": 1500
            }
        },
        "blacklisted_tokens": [
            "0x0000000000000000000000000000000000000000",  # Null address
            "0xdead000000000000000042069420694206942069",  # Known scam
        ],
        "protocol_risk_scores": {
            "aave": 15,
            "compound": 10,
            "uniswap": 12,
            "sushiswap": 15,
            "curve": 10,
            "balancer": 12,
            "maker": 8,
            "unknown": 50,
            "new_protocol": 40
        },
        "suspicious_patterns": {
            "rapid_swap": 30,
            "liquidation_chain": 40,
            "unknown_transaction": 25,
            "high_frequency": 35
        },
        "transaction_count_thresholds": {
            "suspicious_low": 5,
            "suspicious_high": 500
        }
    }
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None
    ):
        """
        Initialize the rule engine.
        
        Args:
            config: Configuration dictionary (overrides default)
            config_file: Path to JSON configuration file
            
        Raises:
            FileNotFoundError: If config_file specified but not found
            ValueError: If configuration is invalid
        """
        logger.info("Initializing RuleEngine...")
        
        # Load configuration
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file:
            self._load_config_file(config_file)
        
        if config:
            self._merge_config(config)
        
        # Custom rules registry
        self.custom_rules: Dict[str, Callable] = {}
        
        logger.info(f"RuleEngine initialized with {len(self.config['chains'])} chains")
    
    def _load_config_file(self, config_file: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_file}. Using defaults.")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            self._merge_config(file_config)
            logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration with existing config.
        
        Args:
            new_config: Configuration to merge
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def assess(self, request: AssessmentRequest) -> AssessmentResponse:
        """
        Perform comprehensive risk assessment on a transaction.
        
        This method chains multiple rule checks and aggregates the results
        into a final risk score with detailed violation tracking.
        
        Args:
            request: Transaction assessment request
            
        Returns:
            AssessmentResponse with score, violations, and details
        """
        logger.info(
            f"Assessing transaction: {request.transaction_type} on {request.chain}, "
            f"amount={request.loan_amount}"
        )
        
        violations: List[str] = []
        details: Dict[str, RuleCheckResult] = {}
        total_penalty = 0
        
        # Rule 1: Check loan amount
        loan_check = self._check_loan_amount(request)
        details["loan_amount_check"] = loan_check
        if not loan_check.passed:
            violations.append("high_loan_amount")
            total_penalty += loan_check.penalty
        
        # Rule 2: Check token blacklist
        token_check = self._check_token_blacklist(request)
        details["token_check"] = token_check
        if not token_check.passed:
            violations.append("blacklisted_token")
            total_penalty += token_check.penalty
        
        # Rule 3: Check protocol risk
        protocol_check = self._check_protocol_risk(request)
        details["protocol_check"] = protocol_check
        if not protocol_check.passed:
            violations.append(f"{request.protocol}_protocol_risk")
            total_penalty += protocol_check.penalty
        
        # Rule 4: Check transaction type patterns
        tx_type_check = self._check_transaction_type(request)
        details["transaction_type_check"] = tx_type_check
        if not tx_type_check.passed:
            violations.append("suspicious_transaction_type")
            total_penalty += tx_type_check.penalty
        
        # Rule 5: Check transaction count anomalies
        tx_count_check = self._check_transaction_count(request)
        details["transaction_count_check"] = tx_count_check
        if not tx_count_check.passed:
            violations.append("unusual_transaction_count")
            total_penalty += tx_count_check.penalty
        
        # Rule 6: Execute custom rules
        for rule_name, rule_func in self.custom_rules.items():
            try:
                custom_check = rule_func(request, self.config)
                details[f"custom_{rule_name}"] = custom_check
                if not custom_check.passed:
                    violations.append(f"custom_{rule_name}")
                    total_penalty += custom_check.penalty
            except Exception as e:
                logger.error(f"Error executing custom rule '{rule_name}': {e}")
        
        # Calculate final score (capped at 100)
        final_score = min(100, total_penalty)
        
        # Determine risk level
        if final_score >= 70:
            risk_level = "HIGH"
        elif final_score >= 40:
            risk_level = "MEDIUM"
        elif final_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        logger.info(
            f"Assessment complete. Score: {final_score}, "
            f"Risk: {risk_level}, Violations: {len(violations)}"
        )
        
        return AssessmentResponse(
            score=final_score,
            violations=violations,
            details=details,
            risk_level=risk_level
        )
    
    def _check_loan_amount(self, request: AssessmentRequest) -> RuleCheckResult:
        """
        Check if loan amount exceeds chain-specific limits.
        
        Args:
            request: Assessment request
            
        Returns:
            RuleCheckResult indicating pass/fail and penalty
        """
        chain_config = self.config["chains"].get(request.chain.value, {})
        max_amount = chain_config.get("max_loan_amount", 1_000_000)
        
        if request.loan_amount > max_amount:
            # Penalty scales with how much the limit is exceeded
            excess_ratio = request.loan_amount / max_amount
            penalty = min(40, int(20 * excess_ratio))
            
            logger.warning(
                f"Loan amount {request.loan_amount} exceeds {request.chain} "
                f"limit of {max_amount}"
            )
            
            return RuleCheckResult(
                passed=False,
                penalty=penalty,
                message=f"Exceeds max loan amount for {request.chain} ({max_amount})"
            )
        
        return RuleCheckResult(passed=True, penalty=0)
    
    def _check_token_blacklist(self, request: AssessmentRequest) -> RuleCheckResult:
        """
        Check if token is blacklisted.
        
        Args:
            request: Assessment request
            
        Returns:
            RuleCheckResult indicating pass/fail and penalty
        """
        blacklist = [t.lower() for t in self.config.get("blacklisted_tokens", [])]
        
        if request.token.lower() in blacklist:
            logger.warning(f"Blacklisted token detected: {request.token}")
            
            return RuleCheckResult(
                passed=False,
                penalty=50,  # High penalty for blacklisted tokens
                message=f"Token {request.token} is blacklisted"
            )
        
        return RuleCheckResult(passed=True, penalty=0)
    
    def _check_protocol_risk(self, request: AssessmentRequest) -> RuleCheckResult:
        """
        Evaluate protocol risk score.
        
        Args:
            request: Assessment request
            
        Returns:
            RuleCheckResult with protocol-specific penalty
        """
        risk_scores = self.config.get("protocol_risk_scores", {})
        protocol_risk = risk_scores.get(
            request.protocol.lower(),
            risk_scores.get("unknown", 50)
        )
        
        # Protocols with risk > 20 are considered high risk
        if protocol_risk > 20:
            logger.warning(
                f"High-risk protocol detected: {request.protocol} "
                f"(risk score: {protocol_risk})"
            )
            
            return RuleCheckResult(
                passed=False,
                penalty=protocol_risk,
                message=f"Protocol {request.protocol} has high risk score ({protocol_risk})"
            )
        
        # Even low-risk protocols contribute some penalty
        return RuleCheckResult(
            passed=True,
            penalty=protocol_risk,
            message=f"Protocol risk score: {protocol_risk}"
        )
    
    def _check_transaction_type(self, request: AssessmentRequest) -> RuleCheckResult:
        """
        Check for suspicious transaction type patterns.
        
        Args:
            request: Assessment request
            
        Returns:
            RuleCheckResult indicating pattern detection
        """
        patterns = self.config.get("suspicious_patterns", {})
        
        # Map transaction types to suspicious patterns
        type_pattern_map = {
            TransactionType.LIQUIDATION: "liquidation_chain",
            TransactionType.UNKNOWN: "unknown_transaction",
            TransactionType.SWAP: "rapid_swap"
        }
        
        pattern_key = type_pattern_map.get(request.transaction_type)
        
        if pattern_key and pattern_key in patterns:
            penalty = patterns[pattern_key]
            logger.warning(
                f"Suspicious transaction type detected: {request.transaction_type}"
            )
            
            return RuleCheckResult(
                passed=False,
                penalty=penalty,
                message=f"Suspicious pattern: {pattern_key}"
            )
        
        return RuleCheckResult(passed=True, penalty=0)
    
    def _check_transaction_count(self, request: AssessmentRequest) -> RuleCheckResult:
        """
        Check for unusual transaction count patterns.
        
        Args:
            request: Assessment request
            
        Returns:
            RuleCheckResult indicating anomaly detection
        """
        thresholds = self.config.get("transaction_count_thresholds", {})
        chain_config = self.config["chains"].get(request.chain.value, {})
        
        low_threshold = thresholds.get("suspicious_low", 5)
        high_threshold = chain_config.get("max_transaction_count", 1000)
        
        # Very low count (possible new/test account)
        if request.transaction_count < low_threshold:
            logger.warning(
                f"Suspiciously low transaction count: {request.transaction_count}"
            )
            return RuleCheckResult(
                passed=False,
                penalty=15,
                message=f"Transaction count below threshold ({low_threshold})"
            )
        
        # Very high count (possible bot/attack)
        if request.transaction_count > high_threshold:
            excess_ratio = request.transaction_count / high_threshold
            penalty = min(35, int(15 * excess_ratio))
            
            logger.warning(
                f"Suspiciously high transaction count: {request.transaction_count}"
            )
            return RuleCheckResult(
                passed=False,
                penalty=penalty,
                message=f"Transaction count exceeds threshold ({high_threshold})"
            )
        
        return RuleCheckResult(passed=True, penalty=0)
    
    def add_rule(
        self,
        rule_name: str,
        rule_func: Callable[[AssessmentRequest, Dict], RuleCheckResult]
    ) -> None:
        """
        Add a custom rule to the engine.
        
        Custom rules are executed after built-in rules and follow the same
        pattern: receive request and config, return RuleCheckResult.
        
        Args:
            rule_name: Unique name for the rule
            rule_func: Function implementing the rule logic
            
        Example:
            def check_gas_price(request, config):
                if request.gas_price > 200:
                    return RuleCheckResult(passed=False, penalty=20)
                return RuleCheckResult(passed=True, penalty=0)
            
            engine.add_rule("high_gas_price", check_gas_price)
        """
        self.custom_rules[rule_name] = rule_func
        logger.info(f"Custom rule added: {rule_name}")
    
    def get_chain_config(self, chain: Chain) -> Dict[str, Any]:
        """
        Get configuration for a specific chain.
        
        Args:
            chain: Blockchain network
            
        Returns:
            Chain-specific configuration
        """
        return self.config["chains"].get(chain.value, {})
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update engine configuration at runtime.
        
        Args:
            updates: Configuration updates to apply
        """
        self._merge_config(updates)
        logger.info("Configuration updated")


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = RuleEngine()
    
    # Example assessment
    request = AssessmentRequest(
        loan_amount=1_000_000,
        token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        protocol="aave",
        transaction_type=TransactionType.SWAP,
        chain=Chain.ETHEREUM,
        transaction_count=50
    )
    
    # Perform assessment
    result = engine.assess(request)
    
    print("\n=== Risk Assessment Result ===")
    print(f"Score: {result.score}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Violations: {result.violations}")
    print("\nDetails:")
    for check_name, check_result in result.details.items():
        status = "✓" if check_result.passed else "✗"
        print(f"  {status} {check_name}: penalty={check_result.penalty}")
        if check_result.message:
            print(f"    → {check_result.message}")
