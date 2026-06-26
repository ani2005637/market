import datetime
from typing import List, Optional
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import pandas as pd

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Auth dependencies
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from backend.config import settings
from backend.db import engine, Base, get_db
from backend.models import User, Signal, MLModelStatus
from backend.schemas import (
    SignalCreate, SignalResponse, ScoreRequest, ScoreResponse,
    TrainRequest, TrainResponse, SignalOutcomeUpdate, Token, UserResponse
)
from backend.ml.engine import ml_engine

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

# Setup password hashing using built-in hashlib to avoid passlib-bcrypt version issues
import hashlib

def get_password_hash(password: str) -> str:
    salt = "sannainnovations_salt_123"
    hash_obj = hashlib.sha256((password + salt).encode('utf-8'))
    return hash_obj.hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=settings.PROJECT_NAME)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Seed default admin user on startup if not present
@app.on_event("startup")
def seed_admin_user():
    db = next(get_db())
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        hashed_pw = get_password_hash("admin123")
        db_user = User(username="admin", hashed_password=hashed_pw, is_active=True)
        db.add(db_user)
        db.commit()
        print("Default admin user created: admin / admin123")
    db.close()

# --- AUTH ENDPOINTS ---
@app.post(f"{settings.API_V1_STR}/auth/login", response_model=Token)
@limiter.limit("10 per minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get(f"{settings.API_V1_STR}/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- SIGNAL & SCORING ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/score", response_model=ScoreResponse)
@limiter.limit("30 per minute")
async def score_setup(request: Request, payload: ScoreRequest):
    """
    Simulates setup scoring on-the-fly without saving to the database.
    Useful for testing from indicators or dashboards.
    """
    data = payload.dict()
    prob, score = ml_engine.predict_probability(data)
    features = ml_engine.extract_features(data)
    
    return {
        "probability_score": prob,
        "setup_score": score,
        "features": features
    }

@app.post(f"{settings.API_V1_STR}/signals", response_model=SignalResponse)
@limiter.limit("60 per minute")
async def receive_webhook_signal(request: Request, payload: SignalCreate, db: Session = Depends(get_db)):
    """
    Receives alerts/webhook setups from TradingView.
    Computes rule-based setup score and ML probability, then saves to DB.
    """
    data = payload.dict()
    
    # Calculate scores
    prob, setup_score = ml_engine.predict_probability(data)
    
    # Create Signal in database
    db_signal = Signal(
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        direction=payload.direction,
        sweep_price=payload.sweep_price,
        mss_price=payload.mss_price,
        trigger_price=payload.trigger_price,
        sweep_depth=payload.sweep_depth,
        atr=payload.atr,
        volume_spike=payload.volume_spike,
        mss_strength=payload.mss_strength,
        trend=payload.trend,
        session=payload.session,
        fvg_size=payload.fvg_size,
        fvg_low=payload.fvg_low,
        fvg_high=payload.fvg_high,
        probability_score=prob,
        setup_score=setup_score,
        status="Pending"
    )
    
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    
    return db_signal

@app.get(f"{settings.API_V1_STR}/signals", response_model=List[SignalResponse])
async def get_signals(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Fetches the history of logged signals.
    """
    query = db.query(Signal)
    if symbol:
        query = query.filter(Signal.symbol == symbol)
    if status:
        query = query.filter(Signal.status == status)
        
    return query.order_by(Signal.timestamp.desc()).limit(limit).all()

@app.put(f"{settings.API_V1_STR}/signals/{{signal_id}}/outcome", response_model=SignalResponse)
async def update_signal_outcome(
    signal_id: int, 
    payload: SignalOutcomeUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the outcome of an active signal (TP Hit or SL Hit).
    This sets the label (outcome=1 or 0) for future ML retraining.
    """
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
        
    signal.status = payload.status
    if payload.status == "TP Hit":
        signal.outcome = 1
    elif payload.status == "SL Hit":
        signal.outcome = 0
    else:
        signal.outcome = None # Reset if marked Pending
        
    db.commit()
    db.refresh(signal)
    return signal

# --- TRAINING ENDPOINTS ---

@app.get(f"{settings.API_V1_STR}/model/status")
async def get_active_model_status(db: Session = Depends(get_db)):
    """
    Fetches the currently active model parameters and training status.
    """
    status_record = db.query(MLModelStatus).filter(MLModelStatus.is_active == True).order_by(MLModelStatus.trained_at.desc()).first()
    
    # Check if files exist
    model_loaded = os.path.exists(ml_engine.model_path) and os.path.exists(ml_engine.scaler_path)
    
    if not status_record:
        return {
            "model_available": model_loaded,
            "trained_at": None,
            "accuracy": 0.0,
            "f1_score": 0.0,
            "roc_auc": 0.0,
            "dataset_size": 0,
            "message": "Model not trained yet in database status." if not model_loaded else "Model loaded from local disk."
        }
        
    return {
        "model_available": model_loaded,
        "trained_at": status_record.trained_at.isoformat(),
        "accuracy": status_record.accuracy,
        "f1_score": status_record.f1_score,
        "roc_auc": status_record.roc_auc,
        "dataset_size": status_record.dataset_size,
        "message": "Model is active and ready."
    }

@app.post(f"{settings.API_V1_STR}/train", response_model=TrainResponse)
@limiter.limit("5 per minute")
async def train_model(
    request: Request,
    payload: TrainRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pulls historical setup records from DB. Merges with synthetic data if required,
    and runs the training pipeline to save a new XGBoost model.
    """
    # 1. Fetch labeled signals from DB
    labeled_db_signals = db.query(Signal).filter(Signal.outcome.is_not(None)).all()
    
    # 2. Extract into list of dicts
    db_data = []
    for sig in labeled_db_signals:
        db_data.append({
            "direction": sig.direction,
            "trend": sig.trend,
            "session": sig.session,
            "atr": sig.atr,
            "sweep_depth": sig.sweep_depth,
            "volume_spike": sig.volume_spike,
            "mss_strength": sig.mss_strength,
            "fvg_size": sig.fvg_size,
            "outcome": sig.outcome
        })
        
    # 3. Handle data volume
    df = pd.DataFrame(db_data)
    
    # If request specifies including synthetic data, or if we have fewer than 15 historical setups
    if payload.include_synthetic or len(df) < 15:
        # Load synthetic historical dataset
        csv_path = "./data/historical_setups.csv"
        if os.path.exists(csv_path):
            syn_df = pd.read_csv(csv_path)
            if not df.empty:
                # Merge DB and synthetic
                df = pd.concat([df, syn_df], ignore_index=True)
            else:
                df = syn_df
        else:
            # Generate on the fly
            from scripts.generate_synthetic_data import generate_synthetic_dataset
            syn_df = generate_synthetic_dataset(250)
            df = pd.concat([df, syn_df], ignore_index=True) if not df.empty else syn_df
            
    # 4. Train
    try:
        metrics = ml_engine.train(df)
        
        # Deactivate old status records
        db.query(MLModelStatus).update({MLModelStatus.is_active: False})
        
        # Write new status to DB
        status_record = MLModelStatus(
            accuracy=metrics["accuracy"],
            f1_score=metrics["f1_score"],
            roc_auc=metrics["roc_auc"],
            dataset_size=metrics["dataset_size"],
            is_active=True
        )
        db.add(status_record)
        db.commit()
        
        return {
            "success": True,
            "message": "Model trained and loaded successfully.",
            "accuracy": metrics["accuracy"],
            "f1_score": metrics["f1_score"],
            "roc_auc": metrics["roc_auc"],
            "dataset_size": metrics["dataset_size"],
            "trained_at": status_record.trained_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model training failed: {str(e)}"
        )

# Serve Frontend static assets
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/")
    async def get_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    @app.get("/")
    async def get_index():
        return JSONResponse(
            status_code=200,
            content={"message": "FastAPI Server is running. Static frontend files directory 'static/' not found."}
        )
