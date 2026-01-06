"""
SQLAlchemy ORM Models for Flash Loan Safety Net

This module defines the database schema for storing flash loan transactions,
risk predictions, and security alerts.

Author: DeFi Flash Loan Security Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Index, Enum, Text, JSON, BigInteger, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func


Base = declarative_base()


# Enums
class RiskLevel(str, enum.Enum):
    """Risk level categories."""
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Chain(str, enum.Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"
    AVALANCHE = "avalanche"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    """Alert status."""
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Transaction(Base):
    """
    Flash loan transaction records.
    
    Stores all monitored flash loan transactions with risk assessments
    and attack detection results.
    """
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction identifiers
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False)
    
    # Addresses
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=True)
    
    # Transaction details
    loan_amount = Column(BigInteger, nullable=False)
    token_address = Column(String(42), nullable=False)
    protocol = Column(String(50), nullable=False)
    chain = Column(Enum(Chain), nullable=False, index=True)
    
    # Risk assessment
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    
    # Attack detection
    is_attack = Column(Boolean, default=False, nullable=False)
    attack_type = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    predictions = relationship(
        "RiskPrediction",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )
    alerts = relationship(
        "Alert",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_chain_created_at', 'chain', 'created_at'),
        Index('ix_risk_score_chain', 'risk_score', 'chain'),
        Index('ix_is_attack_chain', 'is_attack', 'chain'),
    )
    
    @validates('tx_hash')
    def validate_tx_hash(self, key: str, value: str) -> str:
        """Validate transaction hash format."""
        if not value.startswith('0x'):
            raise ValueError("Transaction hash must start with 0x")
        if len(value) != 66:
            raise ValueError("Transaction hash must be 66 characters")
        return value.lower()
    
    @validates('from_address', 'to_address', 'token_address')
    def validate_address(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate Ethereum address format."""
        if value is None:
            return None
        if not value.startswith('0x'):
            raise ValueError(f"{key} must start with 0x")
        if len(value) != 42:
            raise ValueError(f"{key} must be 42 characters")
        return value.lower()
    
    @validates('risk_score')
    def validate_risk_score(self, key: str, value: float) -> float:
        """Validate risk score range."""
        if not 0 <= value <= 100:
            raise ValueError("Risk score must be between 0 and 100")
        return value
    
    def __repr__(self) -> str:
        return (
            f"<Transaction(tx_hash='{self.tx_hash[:10]}...', "
            f"chain='{self.chain.value}', risk_level='{self.risk_level.value}')>"
        )


class RiskPrediction(Base):
    """
    Risk prediction records from ML models.
    
    Stores detailed prediction results including model version,
    input features, and feature importance for explainability.
    """
    __tablename__ = "risk_predictions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique prediction identifier
    prediction_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign key to transaction
    transaction_id = Column(
        Integer,
        ForeignKey('transactions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Model information
    ml_model_version = Column(String(50), nullable=False)
    
    # Prediction data (stored as JSON)
    input_features = Column(JSON, nullable=False)
    output_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    
    # Additional prediction metadata
    rule_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    combined_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    transaction = relationship("Transaction", back_populates="predictions")
    
    # Indexes
    __table_args__ = (
        Index('ix_prediction_created_at', 'created_at'),
        Index('ix_prediction_output_score', 'output_score'),
    )
    
    @validates('output_score', 'confidence', 'rule_score', 'sentiment_score', 'combined_score')
    def validate_score(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate score ranges."""
        if value is None:
            return None
        if key == 'confidence':
            if not 0 <= value <= 1:
                raise ValueError(f"{key} must be between 0 and 1")
        else:
            if not 0 <= value <= 100:
                raise ValueError(f"{key} must be between 0 and 100")
        return value
    
    def __repr__(self) -> str:
        return (
            f"<RiskPrediction(prediction_id='{self.prediction_id}', "
            f"score={self.output_score:.2f}, confidence={self.confidence:.2f})>"
        )


class Alert(Base):
    """
    Security alerts for high-risk transactions.
    
    Stores alerts triggered by risk assessment system with
    severity levels and acknowledgment tracking.
    """
    __tablename__ = "alerts"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Alert details
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(
        Enum(AlertStatus),
        default=AlertStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Foreign key to transaction
    transaction_id = Column(
        Integer,
        ForeignKey('transactions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Alert content
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Timestamps
    triggered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Acknowledgment info
    acknowledged_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    transaction = relationship("Alert", back_populates="alerts")
    
    # Composite indexes
    __table_args__ = (
        Index('ix_alert_severity_status', 'severity', 'status'),
        Index('ix_alert_triggered_at', 'triggered_at'),
        Index('ix_alert_status_triggered', 'status', 'triggered_at'),
    )
    
    def acknowledge(self, acknowledged_by: str) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = acknowledged_by
    
    def resolve(self, resolution_notes: Optional[str] = None) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        if resolution_notes:
            self.resolution_notes = resolution_notes
    
    def dismiss(self, resolution_notes: Optional[str] = None) -> None:
        """Dismiss alert."""
        self.status = AlertStatus.DISMISSED
        self.resolved_at = datetime.utcnow()
        if resolution_notes:
            self.resolution_notes = resolution_notes
    
    def __repr__(self) -> str:
        return (
            f"<Alert(type='{self.alert_type}', "
            f"severity='{self.severity.value}', status='{self.status.value}')>"
        )


# Database initialization helper
def init_db(engine):
    """
    Initialize database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)


# Example usage
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:', echo=True)
    
    # Create tables
    init_db(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Example: Create a transaction
    tx = Transaction(
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        block_number=19251000,
        from_address="0x742d35cc6634c0532925a3b844bc9e7595f0beb",
        to_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        loan_amount=1000000,
        token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        protocol="aave",
        chain=Chain.ETHEREUM,
        risk_score=75.5,
        risk_level=RiskLevel.HIGH,
        is_attack=False
    )
    
    session.add(tx)
    session.commit()
    
    # Example: Create a risk prediction
    prediction = RiskPrediction(
        prediction_id="pred_abc123",
        transaction_id=tx.id,
        ml_model_version="xgboost_v1.0",
        input_features={
            "loan_amount": 1000000,
            "token_volatility": 5.0,
            "protocol_risk_score": 15
        },
        output_score=75.5,
        confidence=0.92,
        feature_importance={
            "loan_amount": 0.30,
            "protocol_risk_score": 0.25
        }
    )
    
    session.add(prediction)
    session.commit()
    
    # Example: Create an alert
    alert = Alert(
        alert_type="high_risk_transaction",
        severity=AlertSeverity.CRITICAL,
        transaction_id=tx.id,
        message="High-risk flash loan detected on Ethereum",
        details={
            "risk_score": 75.5,
            "violations": ["high_loan_amount", "protocol_risk"]
        }
    )
    
    session.add(alert)
    session.commit()
    
    print("\n=== Database Example ===")
    print(f"Transaction: {tx}")
    print(f"Prediction: {prediction}")
    print(f"Alert: {alert}")
    
    # Query example
    high_risk_txs = session.query(Transaction).filter(
        Transaction.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
    ).all()
    
    print(f"\nHigh-risk transactions: {len(high_risk_txs)}")
    
    session.close()
