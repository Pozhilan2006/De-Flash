@echo off
REM Setup script for Risk Prediction Service

echo ========================================
echo Installing Risk Prediction Service
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install -q fastapi uvicorn pydantic xgboost scikit-learn numpy pandas shap redis python-dotenv

echo.
echo [2/3] Verifying installation...
python -c "from risk_prediction_service import RiskPredictionService, LoanRequest; print('✓ Service imports successfully')"

echo.
echo [3/3] Running example tests...
python example_usage.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
