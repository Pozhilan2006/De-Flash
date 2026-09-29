"""
Example usage of the RiskPredictionService.

This script demonstrates how to use the risk prediction service
with various scenarios and edge cases.
"""

import json
from risk_prediction_service import RiskPredictionService, LoanRequest


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main():
    """Run example predictions with various scenarios."""
    
    # Initialize the service
    print_section("Initializing Risk Prediction Service")
    service = RiskPredictionService()
    
    # Example 1: Standard flash loan request
    print_section("Example 1: Standard Flash Loan Request")
    request1 = LoanRequest(
        loan_amount=1_000_000,
        token_volatility=5.0,
        protocol_risk_score=45,
        is_stablecoin=True,
        gas_price=50.0,
        transaction_count=100
    )
    
    prediction1 = service.predict(request1)
    print("\nInput:")
    print(json.dumps(request1.model_dump(), indent=2))
    print("\nOutput:")
    print(json.dumps(prediction1.model_dump(), indent=2))
    
    # Example 2: High-risk scenario
    print_section("Example 2: High-Risk Scenario")
    request2 = LoanRequest(
        loan_amount=5_000_000,
        token_volatility=85.0,
        protocol_risk_score=75,
        is_stablecoin=False,
        gas_price=200.0,
        transaction_count=500
    )
    
    prediction2 = service.predict(request2)
    print("\nInput:")
    print(json.dumps(request2.model_dump(), indent=2))
    print("\nOutput:")
    print(json.dumps(prediction2.model_dump(), indent=2))
    
    # Example 3: Low-risk scenario (stablecoin, low volatility)
    print_section("Example 3: Low-Risk Scenario")
    request3 = LoanRequest(
        loan_amount=100_000,
        token_volatility=2.0,
        protocol_risk_score=15,
        is_stablecoin=True,
        gas_price=30.0,
        transaction_count=50
    )
    
    prediction3 = service.predict(request3)
    print("\nInput:")
    print(json.dumps(request3.model_dump(), indent=2))
    print("\nOutput:")
    print(json.dumps(prediction3.model_dump(), indent=2))
    
    # Example 4: Detailed explanation
    print_section("Example 4: Detailed Prediction Explanation")
    explanation = service.explain_prediction(request1)
    
    print("\nExplanation Text:")
    print(explanation['explanation_text'])
    
    print("\nFeature Importance (Ranked):")
    for i, feature in enumerate(explanation['feature_importance'], 1):
        print(f"{i}. {feature['feature']}: "
              f"weight={feature['weight']:.3f}, "
              f"contribution={feature['contribution']:.2f}")
    
    if 'shap_values' in explanation:
        print("\nSHAP Values:")
        for feature, value in explanation['shap_values'].items():
            print(f"  {feature}: {value:.4f}")
    
    # Example 5: Edge case - minimal values
    print_section("Example 5: Edge Case - Minimal Values")
    request5 = LoanRequest(
        loan_amount=1000,
        token_volatility=0.1,
        protocol_risk_score=5,
        is_stablecoin=True,
        gas_price=10.0,
        transaction_count=1
    )
    
    prediction5 = service.predict(request5)
    print("\nInput:")
    print(json.dumps(request5.model_dump(), indent=2))
    print("\nOutput:")
    print(json.dumps(prediction5.model_dump(), indent=2))
    
    # Example 6: Edge case - extreme values
    print_section("Example 6: Edge Case - Extreme Values")
    request6 = LoanRequest(
        loan_amount=9_000_000,
        token_volatility=95.0,
        protocol_risk_score=95,
        is_stablecoin=False,
        gas_price=450.0,
        transaction_count=9000
    )
    
    prediction6 = service.predict(request6)
    print("\nInput:")
    print(json.dumps(request6.model_dump(), indent=2))
    print("\nOutput:")
    print(json.dumps(prediction6.model_dump(), indent=2))
    
    # Example 7: Testing cache (second call should be faster)
    print_section("Example 7: Cache Performance Test")
    print("\nFirst call (no cache):")
    import time
    start = time.time()
    _ = service.predict(request1)
    first_call_time = time.time() - start
    print(f"Time: {first_call_time:.4f} seconds")
    
    print("\nSecond call (from cache):")
    start = time.time()
    _ = service.predict(request1)
    second_call_time = time.time() - start
    print(f"Time: {second_call_time:.4f} seconds")
    
    if second_call_time < first_call_time:
        speedup = first_call_time / second_call_time
        print(f"\nCache speedup: {speedup:.2f}x faster")
    
    # Summary
    print_section("Summary")
    print("\n✓ Service initialized successfully")
    print(f"✓ ML Model: {'Loaded' if service.use_ml_model else 'Using fallback'}")
    print(f"✓ Redis Cache: {'Enabled' if service.redis_client else 'Disabled'}")
    print(f"✓ SHAP Explainer: {'Available' if service.explainer else 'Not available'}")
    print("\n✓ All examples completed successfully!")
    print("\nThe service is ready for integration into your FastAPI application.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
