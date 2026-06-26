from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class SignalCreate(BaseModel):
    symbol: str = Field(..., example="BTCUSD")
    timeframe: str = Field(..., example="15m")
    direction: str = Field(..., example="Bullish")
    sweep_price: float = Field(..., example=65200.0)
    mss_price: float = Field(..., example=65500.0)
    trigger_price: float = Field(..., example=65400.0)
    sweep_depth: float = Field(..., example=0.15) # depth in % or relative
    atr: float = Field(..., example=120.0)
    volume_spike: float = Field(..., example=1.8) # multiplier of avg volume
    mss_strength: float = Field(..., example=1.5) # multiplier of avg body size
    trend: str = Field(..., example="Bullish") # "Bullish", "Bearish", "Neutral"
    session: str = Field(..., example="London") # "London", "New York", "Asian"
    fvg_size: Optional[float] = Field(None, example=45.0)
    fvg_low: Optional[float] = Field(None, example=65380.0)
    fvg_high: Optional[float] = Field(None, example=65425.0)

class SignalResponse(SignalCreate):
    id: int
    timestamp: datetime
    probability_score: Optional[float] = None
    setup_score: Optional[float] = None
    status: str
    outcome: Optional[int] = None

    class Config:
        from_attributes = True

class ScoreRequest(SignalCreate):
    pass

class ScoreResponse(BaseModel):
    probability_score: float = Field(..., description="ML model success probability (0-100)%")
    setup_score: float = Field(..., description="Rule-based setup score (0-10)")
    features: dict

class TrainRequest(BaseModel):
    include_synthetic: bool = Field(True, description="Whether to include synthetic data if historical dataset is small")

class TrainResponse(BaseModel):
    success: bool
    message: str
    accuracy: float
    f1_score: float
    roc_auc: float
    dataset_size: int
    trained_at: str

class SignalOutcomeUpdate(BaseModel):
    status: str = Field(..., example="TP Hit") # "TP Hit", "SL Hit", "Pending"
