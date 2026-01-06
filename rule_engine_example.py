"""
Example usage of the Rule-Based Risk Assessment Engine.

This script demonstrates various scenarios including:
- Standard assessments
- High-risk scenarios
- Custom rule addition
- Configuration updates
- Integration with ML service
"""

import json
from rule_engine import (
    RuleEngine,
    AssessmentRequest,
    Chain,
    TransactionType,
    RuleCheckResult
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_assessment(result) -> None:
    """Print assessment result in a formatted way."""
    print(f"\nRisk Score: {result.score}/100")
    print(f"Risk Level: {result.risk_level}")
    print(f"Violations: {result.violations if result.violations else 'None'}")
    print("\nRule Check Details:")
    for check_name, check_result in result.details.items():
        status = "✓ PASS" if check_result.passed else "✗ FAIL"
        print(f"  {status} | {check_name}: penalty={check_result.penalty}")
        if check_result.message:
            print(f"         → {check_result.message}")


def main():
    """Run example assessments with various scenarios."""
    
    # Initialize engine with default config
    print_section("Initializing Rule Engine")
    engine = RuleEngine()
    print("✓ Engine initialized with default configuration")
    
    # Example 1: Standard transaction (should pass most checks)
    print_section("Example 1: Standard Transaction (Low Risk)")
    request1 = AssessmentRequest(
        loan_amount=500_000,
        token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        protocol="aave",
        transaction_type=TransactionType.BORROW,
        chain=Chain.ETHEREUM,
        transaction_count=50
    )
    
    result1 = engine.assess(request1)
    print("\nInput:")
    print(json.dumps(request1.model_dump(), indent=2, default=str))
    print_assessment(result1)
    
    # Example 2: High loan amount (exceeds limit)
    print_section("Example 2: High Loan Amount (Exceeds Limit)")
    request2 = AssessmentRequest(
        loan_amount=10_000_000,  # Exceeds Ethereum limit
        token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        protocol="compound",
        transaction_type=TransactionType.FLASH_LOAN,
        chain=Chain.ETHEREUM,
        transaction_count=100
    )
    
    result2 = engine.assess(request2)
    print_assessment(result2)
    
    # Example 3: Blacklisted token
    print_section("Example 3: Blacklisted Token (High Risk)")
    request3 = AssessmentRequest(
        loan_amount=100_000,
        token="0x0000000000000000000000000000000000000000",  # Blacklisted
        protocol="uniswap",
        transaction_type=TransactionType.SWAP,
        chain=Chain.POLYGON,
        transaction_count=25
    )
    
    result3 = engine.assess(request3)
    print_assessment(result3)
    
    # Example 4: Unknown protocol (high risk score)
    print_section("Example 4: Unknown Protocol (High Risk)")
    request4 = AssessmentRequest(
        loan_amount=500_000,
        token="0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        protocol="sketchy_defi_protocol",
        transaction_type=TransactionType.UNKNOWN,
        chain=Chain.ARBITRUM,
        transaction_count=200
    )
    
    result4 = engine.assess(request4)
    print_assessment(result4)
    
    # Example 5: Suspicious transaction pattern
    print_section("Example 5: Suspicious Transaction Pattern")
    request5 = AssessmentRequest(
        loan_amount=800_000,
        token="0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        protocol="sushiswap",
        transaction_type=TransactionType.LIQUIDATION,
        chain=Chain.OPTIMISM,
        transaction_count=3  # Very low, suspicious
    )
    
    result5 = engine.assess(request5)
    print_assessment(result5)
    
    # Example 6: Multiple violations
    print_section("Example 6: Multiple Violations (Very High Risk)")
    request6 = AssessmentRequest(
        loan_amount=8_000_000,  # Exceeds limit
        token="0xdead000000000000000042069420694206942069",  # Blacklisted
        protocol="unknown",  # High risk
        transaction_type=TransactionType.UNKNOWN,  # Suspicious
        chain=Chain.POLYGON,
        transaction_count=2000  # Too high
    )
    
    result6 = engine.assess(request6)
    print_assessment(result6)
    
    # Example 7: Custom rule addition
    print_section("Example 7: Adding Custom Rule")
    
    def check_gas_price(request, config):
        """Custom rule to check gas price."""
        # Simulate gas price check (would need to be in request model)
        # For demo, we'll check transaction count as proxy
        if request.transaction_count > 800:
            return RuleCheckResult(
                passed=False,
                penalty=20,
                message="High gas price detected (simulated)"
            )
        return RuleCheckResult(passed=True, penalty=0)
    
    engine.add_rule("high_gas_price", check_gas_price)
    print("✓ Added custom rule: high_gas_price")
    
    request7 = AssessmentRequest(
        loan_amount=1_000_000,
        token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        protocol="aave",
        transaction_type=TransactionType.SWAP,
        chain=Chain.ETHEREUM,
        transaction_count=900  # Will trigger custom rule
    )
    
    result7 = engine.assess(request7)
    print_assessment(result7)
    
    # Example 8: Configuration update at runtime
    print_section("Example 8: Runtime Configuration Update")
    
    print("\nOriginal Ethereum max loan amount:", 
          engine.get_chain_config(Chain.ETHEREUM)["max_loan_amount"])
    
    engine.update_config({
        "chains": {
            "ethereum": {
                "max_loan_amount": 10_000_000  # Increase limit
            }
        }
    })
    
    print("Updated Ethereum max loan amount:", 
          engine.get_chain_config(Chain.ETHEREUM)["max_loan_amount"])
    
    # Re-assess request2 with new config
    result8 = engine.assess(request2)
    print("\nRe-assessment with updated config:")
    print_assessment(result8)
    
    # Example 9: Loading from config file
    print_section("Example 9: Loading from Configuration File")
    
    try:
        engine_from_file = RuleEngine(config_file="rule_config.json")
        print("✓ Engine loaded from rule_config.json")
        
        result9 = engine_from_file.assess(request1)
        print("\nAssessment with file-based config:")
        print_assessment(result9)
    except Exception as e:
        print(f"Note: Config file not found or error: {e}")
        print("Using default configuration instead")
    
    # Example 10: Integration with ML Service
    print_section("Example 10: Integration with ML Service")
    
    print("\nDemonstrating combined risk assessment:")
    print("Rule Engine Score:", result1.score)
    print("Rule Engine Risk Level:", result1.risk_level)
    
    # Simulate ML service prediction
    ml_score = 45.7  # Would come from risk_prediction_service
    ml_confidence = 0.92
    
    print(f"\nML Service Score: {ml_score}")
    print(f"ML Service Confidence: {ml_confidence}")
    
    # Combined scoring strategy
    combined_score = (result1.score * 0.4) + (ml_score * 0.6)
    print(f"\nCombined Score (40% rules, 60% ML): {combined_score:.1f}")
    
    if combined_score >= 70:
        combined_risk = "HIGH"
    elif combined_score >= 40:
        combined_risk = "MEDIUM"
    else:
        combined_risk = "LOW"
    
    print(f"Combined Risk Level: {combined_risk}")
    
    # Summary
    print_section("Summary")
    print("\n✓ All examples completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Chain-specific rule configurations")
    print("  • Token blacklist enforcement")
    print("  • Protocol risk scoring")
    print("  • Transaction pattern detection")
    print("  • Transaction count anomaly detection")
    print("  • Custom rule addition")
    print("  • Runtime configuration updates")
    print("  • Configuration file loading")
    print("  • Integration with ML service")
    print("\nThe rule engine is ready for integration into your application!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
