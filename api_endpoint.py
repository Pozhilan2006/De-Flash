"""
FastAPI Risk Prediction Endpoint

This module provides a complete FastAPI endpoint for flash loan risk prediction,
combining ML predictions, rule-based assessment, and sentiment analysis.

Author: DeFi Flash Loan Security Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Import our services
from risk_prediction_service import RiskPredictionService, LoanRequest
from rule_engine import RuleEngine, AssessmentRequest, Chain, TransactionType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Enums for validation
class ProtocolEnum(str, Enum):
    """Supported DeFi protocols."""
    AAVE = "aave"
    DYDX = "dydx"
    UNISWAP = "uniswap"
    CURVE = "curve"
    COMPOUND = "compound"
    SUSHISWAP = "sushiswap"
    BALANCER = "balancer"
    OTHER = "other"


class TransactionTypeEnum(str, Enum):
    """Transaction types for classification."""
    SWAP = "swap"
    LIQUIDATION = "liquidation"
    ARBITRAGE = "arbitrage"
    EXPLOIT = "exploit"
    BORROW = "borrow"
    LEND = "lend"


class ChainEnum(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


# Request/Response Models
class RiskPredictionRequest(BaseModel):
    """Request model for risk prediction endpoint."""
    loan_amount: int = Field(gt=0, le=10_000_000_000, description="Loan amount in USD")
    token: str = Field(min_length=42, max_length=42, description="ERC20 token address")
    protocol: ProtocolEnum = Field(description="DeFi protocol name")
    transaction_type: TransactionTypeEnum = Field(description="Transaction type")
    chain: ChainEnum = Field(description="Blockchain network")
    token_volatility: Optional[float] = Field(default=5.0, ge=0, le=100)
    gas_price: Optional[float] = Field(default=50.0, gt=0)
    transaction_count: Optional[int] = Field(default=100, ge=0)
    
    @field_validator('token')
    @classmethod
    def validate_token_address(cls, v: str) -> str:
        """Validate ERC20 address format."""
        if not v.startswith('0x'):
            raise ValueError("Token address must start with 0x")
        if len(v) != 42:
            raise ValueError("Token address must be 42 characters (0x + 40 hex)")
        try:
            int(v[2:], 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError("Token address must contain valid hexadecimal characters")
        return v.lower()


class RiskFactors(BaseModel):
    """Risk factors breakdown."""
    ml_factors: dict
    rule_violations: list[str]
    combined_factors: list[str]


class RiskPredictionData(BaseModel):
    """Risk prediction data response."""
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    confidence: float = Field(ge=0, le=1)
    factors: list[str]
    ml_score: float
    rule_score: int
    sentiment_score: float
    prediction_id: str


class RiskPredictionResponse(BaseModel):
    """Success response model."""
    success: bool = True
    data: RiskPredictionData
    timestamp: str


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: ErrorDetail


# Initialize FastAPI app
app = FastAPI(
    title="Flash Loan Risk Prediction API",
    description="ML-powered risk assessment for flash loan transactions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
logger.info("Initializing services...")
ml_service = RiskPredictionService()
rule_engine = RuleEngine(config_file="rule_config.json")
logger.info("Services initialized successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Flash Loan Risk Prediction API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ml_service": ml_service.use_ml_model,
        "rule_engine": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post(
    "/risk/predict",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def predict_risk(request: RiskPredictionRequest):
    """
    Predict flash loan transaction risk.
    
    This endpoint combines ML predictions, rule-based assessment, and sentiment
    analysis to provide a comprehensive risk score.
    
    **Scoring Weights:**
    - ML Model: 60%
    - Rule Engine: 30%
    - Sentiment: 10%
    
    **Risk Levels:**
    - MINIMAL: 0-20
    - LOW: 20-40
    - MEDIUM: 40-70
    - HIGH: 70-85
    - CRITICAL: 85-100
    """
    try:
        logger.info(f"Processing risk prediction request for {request.chain}/{request.protocol}")
        
        # Step 1: ML Prediction
        try:
            ml_request = LoanRequest(
                loan_amount=float(request.loan_amount),
                token_volatility=request.token_volatility,
                protocol_risk_score=_get_protocol_risk_score(request.protocol),
                is_stablecoin=_is_stablecoin(request.token),
                gas_price=request.gas_price,
                transaction_count=request.transaction_count
            )
            
            ml_result = ml_service.predict(ml_request)
            ml_score = ml_result.risk_score
            confidence = ml_result.confidence
            
            logger.info(f"ML prediction: {ml_score:.2f} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "ML_PREDICTION_FAILED",
                    "message": f"ML service error: {str(e)}"
                }
            )
        
        # Step 2: Rule-Based Assessment
        try:
            # Map enums to rule engine types
            tx_type_map = {
                TransactionTypeEnum.SWAP: TransactionType.SWAP,
                TransactionTypeEnum.LIQUIDATION: TransactionType.LIQUIDATION,
                TransactionTypeEnum.ARBITRAGE: TransactionType.ARBITRAGE,
                TransactionTypeEnum.EXPLOIT: TransactionType.UNKNOWN,
                TransactionTypeEnum.BORROW: TransactionType.BORROW,
                TransactionTypeEnum.LEND: TransactionType.LEND,
            }
            
            chain_map = {
                ChainEnum.ETHEREUM: Chain.ETHEREUM,
                ChainEnum.POLYGON: Chain.POLYGON,
                ChainEnum.ARBITRUM: Chain.ARBITRUM,
                ChainEnum.OPTIMISM: Chain.OPTIMISM,
            }
            
            rule_request = AssessmentRequest(
                loan_amount=float(request.loan_amount),
                token=request.token,
                protocol=request.protocol.value,
                transaction_type=tx_type_map[request.transaction_type],
                chain=chain_map[request.chain],
                transaction_count=request.transaction_count
            )
            
            rule_result = rule_engine.assess(rule_request)
            rule_score = rule_result.score
            
            logger.info(f"Rule assessment: {rule_score} ({rule_result.risk_level})")
            
        except Exception as e:
            logger.error(f"Rule assessment failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "RULE_ASSESSMENT_FAILED",
                    "message": f"Rule engine error: {str(e)}"
                }
            )
        
        # Step 3: Sentiment Analysis (simulated for now)
        sentiment_score = _calculate_sentiment_score(request)
        
        # Step 4: Combine Scores
        combined_score = (
            ml_score * 0.6 +
            rule_score * 0.3 +
            sentiment_score * 0.1
        )
        
        # Determine risk level
        if combined_score >= 85:
            risk_level = "CRITICAL"
        elif combined_score >= 70:
            risk_level = "HIGH"
        elif combined_score >= 40:
            risk_level = "MEDIUM"
        elif combined_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        # Combine factors
        ml_factor = (
            f"ml_confidence_{int(confidence * 100)}"
            if ml_service.use_ml_model
            else "rule_based_fallback_mode"
        )
        factors = list(set(
            rule_result.violations +
            [ml_factor]
        ))
        
        # Generate prediction ID
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
        
        # Build response
        response_data = RiskPredictionData(
            risk_score=round(combined_score, 2),
            risk_level=risk_level,
            confidence=round(confidence, 3),
            factors=factors,
            ml_score=round(ml_score, 2),
            rule_score=rule_score,
            sentiment_score=round(sentiment_score, 2),
            prediction_id=prediction_id
        )
        
        logger.info(
            f"Prediction complete: {prediction_id} | "
            f"Score: {combined_score:.2f} | Level: {risk_level}"
        )
        
        return RiskPredictionResponse(
            success=True,
            data=response_data,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


def _get_protocol_risk_score(protocol: ProtocolEnum) -> float:
    """Get protocol risk score for ML model."""
    scores = {
        ProtocolEnum.AAVE: 15.0,
        ProtocolEnum.COMPOUND: 10.0,
        ProtocolEnum.UNISWAP: 12.0,
        ProtocolEnum.CURVE: 10.0,
        ProtocolEnum.DYDX: 18.0,
        ProtocolEnum.SUSHISWAP: 15.0,
        ProtocolEnum.BALANCER: 12.0,
        ProtocolEnum.OTHER: 50.0,
    }
    return scores.get(protocol, 50.0)


def _is_stablecoin(token_address: str) -> bool:
    """Check if token is a known stablecoin."""
    stablecoins = {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
        "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
        "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
        "0x4fabb145d64652a948d72533023f6e7a623c7c53",  # BUSD
    }
    return token_address.lower() in stablecoins


def _calculate_sentiment_score(request: RiskPredictionRequest) -> float:
    """
    Calculate sentiment score based on market conditions.
    
    This is a simplified version. In production, this would:
    - Analyze social media sentiment
    - Check recent exploit news
    - Monitor protocol TVL changes
    - Track gas price trends
    """
    # Base score
    score = 50.0
    
    # Adjust for transaction type
    if request.transaction_type == TransactionTypeEnum.EXPLOIT:
        score += 30
    elif request.transaction_type == TransactionTypeEnum.LIQUIDATION:
        score += 10
    elif request.transaction_type == TransactionTypeEnum.ARBITRAGE:
        score -= 5
    
    # Adjust for protocol
    if request.protocol in [ProtocolEnum.AAVE, ProtocolEnum.COMPOUND]:
        score -= 10  # Trusted protocols
    elif request.protocol == ProtocolEnum.OTHER:
        score += 20  # Unknown protocols
    
    # Clamp to 0-100
    return round(max(0.0, min(100.0, score)), 2)


# Run with: uvicorn api_endpoint:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
