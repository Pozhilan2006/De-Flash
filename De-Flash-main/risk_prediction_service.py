"""
ML-Based Risk Prediction Service for Flash Loan Security

This module provides a comprehensive risk prediction service using XGBoost
for flash loan transaction analysis. It includes feature engineering,
model-based predictions, SHAP-based explainability, and Redis caching.

Author: DeFi Flash Loan Security Team
Version: 1.0.0
"""

import logging
import pickle
import hashlib
import json
from typing import Dict, Optional, Tuple, Any, List
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available. Install with: pip install xgboost")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Install with: pip install redis")

from pydantic import BaseModel, Field, field_validator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoanRequest(BaseModel):
    """
    Pydantic model for flash loan request validation.
    
    Attributes:
        loan_amount: Amount of the flash loan in USD
        token_volatility: Token volatility percentage (0-100)
        protocol_risk_score: Protocol risk score (0-100)
        is_stablecoin: Whether the token is a stablecoin
        gas_price: Current gas price in Gwei
        transaction_count: Number of transactions in the last hour
    """
    loan_amount: float = Field(gt=0, description="Loan amount in USD")
    token_volatility: float = Field(ge=0, le=100, description="Token volatility %")
    protocol_risk_score: float = Field(ge=0, le=100, description="Protocol risk score")
    is_stablecoin: bool = Field(description="Is stablecoin flag")
    gas_price: float = Field(gt=0, description="Gas price in Gwei")
    transaction_count: int = Field(ge=0, description="Transaction count")

    @field_validator('loan_amount', 'gas_price')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class PredictionResponse(BaseModel):
    """
    Response model for risk predictions.
    
    Attributes:
        risk_score: Overall risk score (0-100)
        confidence: Model confidence (0-1)
        ml_score: Raw ML model score (0-100)
        factors: Dictionary of risk factors with weights and contributions
    """
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    ml_score: int = Field(ge=0, le=100)
    factors: Dict[str, Dict[str, float]]


class RiskPredictionService:
    """
    ML-based risk prediction service for flash loan security analysis.
    
    This service loads a pre-trained XGBoost model and provides risk predictions
    with explainability through SHAP values. It includes Redis caching for
    performance optimization and graceful fallback to rule-based scoring.
    """
    
    # Feature normalization ranges (min, max)
    FEATURE_RANGES = {
        'loan_amount': (0, 10_000_000),
        'token_volatility': (0, 100),
        'protocol_risk_score': (0, 100),
        'is_stablecoin': (0, 1),
        'gas_price': (0, 500),
        'transaction_count': (0, 10_000)
    }
    
    # Feature weights for fallback scoring
    FALLBACK_WEIGHTS = {
        'loan_amount': 0.30,
        'token_volatility': 0.25,
        'protocol_risk_score': 0.25,
        'is_stablecoin': -0.10,  # Negative because stablecoins reduce risk
        'gas_price': 0.05,
        'transaction_count': 0.15
    }
    
    def __init__(
        self,
        model_path: str = "./models_cache/flash_loan_model.pkl",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        cache_ttl: int = 3600
    ):
        """
        Initialize the risk prediction service.
        
        Args:
            model_path: Path to the pre-trained XGBoost model
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            cache_ttl: Cache time-to-live in seconds
            
        Raises:
            Warning if model file not found (falls back to rule-based scoring)
            Warning if Redis connection fails (operates without caching)
        """
        self.model_path = Path(model_path)
        self.model: Optional[Any] = None
        self.explainer: Optional[Any] = None
        self.redis_client: Optional[Any] = None
        self.cache_ttl = cache_ttl
        self.use_ml_model = False
        
        logger.info("Initializing RiskPredictionService...")
        
        # Load XGBoost model
        self._load_model()
        
        # Initialize Redis connection
        self._init_redis(redis_host, redis_port, redis_db)
        
        logger.info(
            f"Service initialized. ML Model: {self.use_ml_model}, "
            f"Redis: {self.redis_client is not None}"
        )
    
    def _load_model(self) -> None:
        """
        Load the pre-trained XGBoost model from disk.
        
        If the model file doesn't exist, logs a warning and falls back
        to rule-based scoring.
        """
        try:
            if not self.model_path.exists():
                logger.warning(
                    f"Model file not found at {self.model_path}. "
                    "Using fallback rule-based scoring."
                )
                return
            
            if not XGBOOST_AVAILABLE:
                logger.warning(
                    "XGBoost not installed. Using fallback rule-based scoring."
                )
                return
            
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Initialize SHAP explainer if available
            if SHAP_AVAILABLE and self.model is not None:
                try:
                    self.explainer = shap.TreeExplainer(self.model)
                    logger.info("SHAP explainer initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize SHAP explainer: {e}")
            
            self.use_ml_model = True
            logger.info(f"XGBoost model loaded successfully from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}. Using fallback scoring.")
            self.model = None
            self.use_ml_model = False
    
    def _init_redis(self, host: str, port: int, db: int) -> None:
        """
        Initialize Redis connection for caching predictions.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis not installed. Caching disabled.")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connected at {host}:{port}/{db}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def predict(self, loan_request: LoanRequest) -> PredictionResponse:
        """
        Generate risk prediction for a flash loan request.
        
        This method first checks the cache, then uses the ML model if available,
        or falls back to rule-based scoring. It returns a comprehensive risk
        assessment with factor contributions.
        
        Args:
            loan_request: Validated loan request parameters
            
        Returns:
            PredictionResponse with risk score, confidence, and factor breakdown
            
        Raises:
            ValueError: If input validation fails
            Exception: For unexpected errors during prediction
        """
        try:
            logger.info(f"Processing prediction for loan amount: {loan_request.loan_amount}")
            
            # Check cache first
            cached_result = self._get_cached_prediction(loan_request)
            if cached_result:
                logger.info("Returning cached prediction")
                return cached_result
            
            # Extract and normalize features
            features, feature_dict = self._extract_features(loan_request)
            
            # Generate prediction
            if self.use_ml_model and self.model is not None:
                risk_score, confidence, factors = self._predict_with_model(
                    features, feature_dict
                )
            else:
                risk_score, confidence, factors = self._calculate_fallback_score(
                    feature_dict
                )
            
            # Create response
            response = PredictionResponse(
                risk_score=round(risk_score, 2),
                confidence=round(confidence, 3),
                ml_score=int(risk_score),
                factors=factors
            )
            
            # Cache the result
            self._cache_prediction(loan_request, response)
            
            logger.info(
                f"Prediction complete. Risk: {response.risk_score}, "
                f"Confidence: {response.confidence}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            raise
    
    def _predict_with_model(
        self,
        features: np.ndarray,
        feature_dict: Dict[str, float]
    ) -> Tuple[float, float, Dict[str, Dict[str, float]]]:
        """
        Generate prediction using the XGBoost model.
        
        Args:
            features: Normalized feature array
            feature_dict: Dictionary of feature names to values
            
        Returns:
            Tuple of (risk_score, confidence, factors_dict)
        """
        try:
            # Convert to DMatrix for XGBoost
            dmatrix = xgb.DMatrix(features.reshape(1, -1))
            
            # Get prediction (probability of high risk)
            prediction = self.model.predict(dmatrix)[0]
            risk_score = float(prediction * 100)
            
            # Confidence is based on distance from decision boundary (0.5)
            confidence = 1.0 - 2 * abs(prediction - 0.5)
            
            # Get feature contributions
            factors = self._get_feature_contributions(features, feature_dict)
            
            return risk_score, confidence, factors
            
        except Exception as e:
            logger.error(f"Model prediction failed: {e}. Using fallback.")
            return self._calculate_fallback_score(feature_dict)
    
    def _get_feature_contributions(
        self,
        features: np.ndarray,
        feature_dict: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate feature contributions to the prediction.
        
        Uses SHAP values if available, otherwise uses feature importance.
        
        Args:
            features: Normalized feature array
            feature_dict: Dictionary of feature names to values
            
        Returns:
            Dictionary mapping feature names to weight and contribution
        """
        factors = {}
        feature_names = list(self.FEATURE_RANGES.keys())
        
        try:
            if self.explainer is not None:
                # Use SHAP values for precise contributions
                shap_values = self.explainer.shap_values(features.reshape(1, -1))
                
                for i, name in enumerate(feature_names):
                    contribution = float(abs(shap_values[0][i]) * 100)
                    factors[name] = {
                        'weight': round(contribution / 100, 3),
                        'contribution': round(contribution, 2)
                    }
            else:
                # Use feature importance from model
                importance = self.model.get_score(importance_type='weight')
                total_importance = sum(importance.values())
                
                for i, name in enumerate(feature_names):
                    feat_importance = importance.get(f'f{i}', 0)
                    weight = feat_importance / total_importance if total_importance > 0 else 0
                    contribution = weight * feature_dict[name] * 100
                    
                    factors[name] = {
                        'weight': round(weight, 3),
                        'contribution': round(contribution, 2)
                    }
        except Exception as e:
            logger.warning(f"Error calculating contributions: {e}. Using defaults.")
            # Fallback to uniform weights
            for name in feature_names:
                factors[name] = {
                    'weight': round(1.0 / len(feature_names), 3),
                    'contribution': round(feature_dict[name] * 100 / len(feature_names), 2)
                }
        
        return factors
    
    def _calculate_fallback_score(
        self,
        feature_dict: Dict[str, float]
    ) -> Tuple[float, float, Dict[str, Dict[str, float]]]:
        """
        Calculate risk score using rule-based approach.
        
        This is used when the ML model is not available. It applies
        weighted scoring based on predefined feature weights.
        
        Args:
            feature_dict: Dictionary of normalized feature values
            
        Returns:
            Tuple of (risk_score, confidence, factors_dict)
        """
        risk_score = 0.0
        factors = {}
        
        for feature, value in feature_dict.items():
            weight = self.FALLBACK_WEIGHTS[feature]
            contribution = value * abs(weight) * 100
            
            # Negative weights reduce risk
            if weight < 0:
                risk_score -= contribution
            else:
                risk_score += contribution
            
            factors[feature] = {
                'weight': round(abs(weight), 3),
                'contribution': round(contribution, 2)
            }
        
        # Normalize to 0-100 range
        risk_score = max(0, min(100, risk_score))
        
        # Lower confidence for rule-based scoring
        confidence = 0.75
        
        logger.info("Using rule-based fallback scoring")
        return risk_score, confidence, factors
    
    def explain_prediction(
        self,
        loan_request: LoanRequest
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation for a prediction.
        
        Provides SHAP values, feature importance, and contribution analysis
        to help understand why a particular risk score was assigned.
        
        Args:
            loan_request: Validated loan request parameters
            
        Returns:
            Dictionary containing:
                - shap_values: SHAP value for each feature (if available)
                - feature_importance: Ranked feature importance
                - prediction_details: Full prediction breakdown
                - explanation_text: Human-readable explanation
        """
        try:
            logger.info("Generating prediction explanation")
            
            # Get prediction
            prediction = self.predict(loan_request)
            
            # Extract features
            features, feature_dict = self._extract_features(loan_request)
            
            explanation = {
                'prediction_details': prediction.model_dump(),
                'feature_values': feature_dict,
                'feature_importance': self._rank_features(prediction.factors),
                'explanation_text': self._generate_explanation_text(
                    prediction, feature_dict
                )
            }
            
            # Add SHAP values if available
            if self.explainer is not None:
                try:
                    shap_values = self.explainer.shap_values(features.reshape(1, -1))
                    explanation['shap_values'] = {
                        name: float(shap_values[0][i])
                        for i, name in enumerate(self.FEATURE_RANGES.keys())
                    }
                except Exception as e:
                    logger.warning(f"Failed to compute SHAP values: {e}")
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            raise
    
    def _rank_features(
        self,
        factors: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Rank features by their contribution to the prediction.
        
        Args:
            factors: Dictionary of feature contributions
            
        Returns:
            List of features sorted by contribution (descending)
        """
        ranked = [
            {
                'feature': name,
                'weight': data['weight'],
                'contribution': data['contribution']
            }
            for name, data in factors.items()
        ]
        
        return sorted(ranked, key=lambda x: x['contribution'], reverse=True)
    
    def _generate_explanation_text(
        self,
        prediction: PredictionResponse,
        feature_dict: Dict[str, float]
    ) -> str:
        """
        Generate human-readable explanation of the prediction.
        
        Args:
            prediction: Prediction response object
            feature_dict: Dictionary of feature values
            
        Returns:
            Human-readable explanation string
        """
        risk_level = "HIGH" if prediction.risk_score > 70 else \
                     "MEDIUM" if prediction.risk_score > 40 else "LOW"
        
        top_factors = self._rank_features(prediction.factors)[:3]
        top_factor_names = [f['feature'] for f in top_factors]
        
        explanation = (
            f"Risk Level: {risk_level} ({prediction.risk_score:.1f}/100)\n"
            f"Confidence: {prediction.confidence:.1%}\n\n"
            f"Top contributing factors:\n"
        )
        
        for i, factor in enumerate(top_factors, 1):
            explanation += (
                f"{i}. {factor['feature']}: "
                f"contribution={factor['contribution']:.1f}, "
                f"weight={factor['weight']:.2f}\n"
            )
        
        return explanation
    
    def _extract_features(
        self,
        loan_request: LoanRequest
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract and normalize features from loan request.
        
        Args:
            loan_request: Validated loan request parameters
            
        Returns:
            Tuple of (normalized_features_array, feature_dict)
        """
        # Create feature dictionary
        feature_dict = {
            'loan_amount': float(loan_request.loan_amount),
            'token_volatility': float(loan_request.token_volatility),
            'protocol_risk_score': float(loan_request.protocol_risk_score),
            'is_stablecoin': float(loan_request.is_stablecoin),
            'gas_price': float(loan_request.gas_price),
            'transaction_count': float(loan_request.transaction_count)
        }
        
        # Normalize features
        normalized_dict = {}
        for feature, value in feature_dict.items():
            normalized_dict[feature] = self._normalize(
                value,
                self.FEATURE_RANGES[feature][0],
                self.FEATURE_RANGES[feature][1]
            )
        
        # Convert to numpy array in correct order
        features = np.array([
            normalized_dict[name] for name in self.FEATURE_RANGES.keys()
        ])
        
        return features, normalized_dict
    
    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """
        Apply min-max normalization to a value.
        
        Args:
            value: Value to normalize
            min_val: Minimum value in range
            max_val: Maximum value in range
            
        Returns:
            Normalized value in [0, 1] range
        """
        if max_val == min_val:
            return 0.0
        
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def _get_cached_prediction(
        self,
        loan_request: LoanRequest
    ) -> Optional[PredictionResponse]:
        """
        Retrieve cached prediction from Redis.
        
        Args:
            loan_request: Loan request parameters
            
        Returns:
            Cached PredictionResponse or None if not found
        """
        if self.redis_client is None:
            return None
        
        try:
            cache_key = self._generate_cache_key(loan_request)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for key: {cache_key}")
                return PredictionResponse(**json.loads(cached_data))
            
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None
    
    def _cache_prediction(
        self,
        loan_request: LoanRequest,
        response: PredictionResponse
    ) -> None:
        """
        Cache prediction result in Redis.
        
        Args:
            loan_request: Loan request parameters
            response: Prediction response to cache
        """
        if self.redis_client is None:
            return
        
        try:
            cache_key = self._generate_cache_key(loan_request)
            cache_value = response.model_dump_json()
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                cache_value
            )
            logger.debug(f"Cached prediction with key: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching prediction: {e}")
    
    @staticmethod
    def _generate_cache_key(loan_request: LoanRequest) -> str:
        """
        Generate unique cache key for a loan request.
        
        Args:
            loan_request: Loan request parameters
            
        Returns:
            MD5 hash of request parameters
        """
        request_str = (
            f"{loan_request.loan_amount}:"
            f"{loan_request.token_volatility}:"
            f"{loan_request.protocol_risk_score}:"
            f"{loan_request.is_stablecoin}:"
            f"{loan_request.gas_price}:"
            f"{loan_request.transaction_count}"
        )
        
        hash_obj = hashlib.md5(request_str.encode())
        return f"risk_pred:{hash_obj.hexdigest()}"


# Example usage
if __name__ == "__main__":
    # Initialize service
    service = RiskPredictionService()
    
    # Create example request
    example_request = LoanRequest(
        loan_amount=1_000_000,
        token_volatility=5.0,
        protocol_risk_score=45,
        is_stablecoin=True,
        gas_price=50.0,
        transaction_count=100
    )
    
    # Get prediction
    prediction = service.predict(example_request)
    print("\n=== Prediction Result ===")
    print(json.dumps(prediction.model_dump(), indent=2))
    
    # Get explanation
    explanation = service.explain_prediction(example_request)
    print("\n=== Explanation ===")
    print(explanation['explanation_text'])
