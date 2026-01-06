# Risk Prediction Service

## Overview
ML-based risk prediction service for flash loan security analysis using XGBoost.

## Features
- ✅ XGBoost model integration with graceful fallback
- ✅ SHAP-based prediction explainability
- ✅ Redis caching for performance
- ✅ Comprehensive error handling and logging
- ✅ Type hints and docstrings throughout
- ✅ Pydantic validation for inputs/outputs

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from risk_prediction_service import RiskPredictionService, LoanRequest

# Initialize service
service = RiskPredictionService()

# Create request
request = LoanRequest(
    loan_amount=1_000_000,
    token_volatility=5.0,
    protocol_risk_score=45,
    is_stablecoin=True,
    gas_price=50.0,
    transaction_count=100
)

# Get prediction
prediction = service.predict(request)
print(f"Risk Score: {prediction.risk_score}")
print(f"Confidence: {prediction.confidence}")

# Get explanation
explanation = service.explain_prediction(request)
print(explanation['explanation_text'])
```

## Running Examples

```bash
python example_usage.py
```

## API Response Format

```json
{
  "risk_score": 45.7,
  "confidence": 0.92,
  "ml_score": 45,
  "factors": {
    "loan_amount": {
      "weight": 0.30,
      "contribution": 10.5
    },
    "protocol_risk_score": {
      "weight": 0.25,
      "contribution": 8.2
    }
  }
}
```

## Configuration

### Model Path
Default: `./models_cache/flash_loan_model.pkl`

### Redis Configuration
- Host: `localhost`
- Port: `6379`
- DB: `0`
- Cache TTL: `3600` seconds

### Custom Configuration

```python
service = RiskPredictionService(
    model_path="./custom/path/model.pkl",
    redis_host="redis.example.com",
    redis_port=6380,
    cache_ttl=7200
)
```

## Graceful Degradation

The service automatically handles:
- Missing XGBoost model → Falls back to rule-based scoring
- Redis unavailable → Operates without caching
- SHAP unavailable → Uses feature importance instead

## Notes

- All predictions are cached for 1 hour by default
- Logs are written to stdout with INFO level
- Input validation via Pydantic ensures data quality
- Thread-safe for concurrent requests
