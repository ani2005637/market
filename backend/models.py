import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from backend.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False) # "Bullish" or "Bearish"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Feature values sent from TradingView or calculated
    sweep_price = Column(Float, nullable=False)
    mss_price = Column(Float, nullable=False)
    trigger_price = Column(Float, nullable=False)
    sweep_depth = Column(Float, nullable=False)  # in % or relative
    atr = Column(Float, nullable=False)
    volume_spike = Column(Float, nullable=False)  # volume / avg_volume
    mss_strength = Column(Float, nullable=False)  # body / avg_body
    trend = Column(String, nullable=False)        # "Bullish", "Bearish", or "Neutral"
    session = Column(String, nullable=False)      # "Asian", "London", "New York"
    fvg_size = Column(Float, nullable=True)       # size of FVG
    fvg_low = Column(Float, nullable=True)
    fvg_high = Column(Float, nullable=True)
    
    # Scoring outputs
    probability_score = Column(Float, nullable=True) # ML predicted probability (0-100)
    setup_score = Column(Float, nullable=True)       # Rule-based setup score (0-10)
    
    # Outcome tracking
    status = Column(String, default="Pending")      # "Pending", "TP Hit", "SL Hit"
    outcome = Column(Integer, nullable=True)        # 1 = Success (TP), 0 = Failure (SL), None = Unlabeled

class MLModelStatus(Base):
    __tablename__ = "ml_model_status"
    
    id = Column(Integer, primary_key=True, index=True)
    trained_at = Column(DateTime, default=datetime.datetime.utcnow)
    accuracy = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    dataset_size = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
