import os
import sys
import random
import pandas as pd
import numpy as np

# Add the parent folder to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.engine import ml_engine
from backend.config import settings

def generate_synthetic_dataset(num_samples: int = 250) -> pd.DataFrame:
    """
    Generates a realistic synthetic historical dataset of TradingView SMC setups
    with success (TP Hit) or failure (SL Hit) labels.
    """
    random.seed(42)
    np.random.seed(42)
    
    symbols = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "XAUUSD"]
    timeframes = ["5m", "15m", "1h", "4h"]
    trends = ["Bullish", "Bearish", "Neutral"]
    sessions = ["Asian", "London", "New York"]
    directions = ["Bullish", "Bearish"]
    
    data = []
    for _ in range(num_samples):
        symbol = random.choice(symbols)
        timeframe = random.choice(timeframes)
        direction = random.choice(directions)
        
        # Trend alignment
        trend = random.choice(trends)
        trend_aligned = 1.0 if trend == direction else (0.5 if trend == "Neutral" else 0.0)
        
        # Session
        session = random.choice(sessions)
        session_strength = 1.0 if session in ["London", "New York"] else 0.5
        
        # Features
        atr = round(random.uniform(10.0, 150.0), 2)
        if "USD" in symbol and "BTC" not in symbol and "ETH" not in symbol:
            # Forex typical ATR in pips (say, 0.0005 to 0.0050)
            atr = round(random.uniform(0.0005, 0.0050), 5)
            
        sweep_depth = round(atr * random.uniform(0.05, 0.5), 5)
        volume_spike = round(random.uniform(0.8, 3.5), 2)
        mss_strength = round(random.uniform(0.8, 3.5), 2)
        
        # FVG size
        has_fvg = random.random() > 0.3
        fvg_size = round(atr * random.uniform(0.1, 0.8), 5) if has_fvg else 0.0
        
        # Base prices
        if "BTC" in symbol:
            base_price = random.uniform(60000, 70000)
        elif "ETH" in symbol:
            base_price = random.uniform(3000, 4000)
        elif "XAU" in symbol:
            base_price = random.uniform(2200, 2400)
        else: # Forex
            base_price = random.uniform(1.05, 1.30)
            
        base_price = round(base_price, 5 if "USD" in symbol and "BTC" not in symbol and "ETH" not in symbol else 2)
        
        if direction == "Bullish":
            sweep_price = round(base_price - sweep_depth, 5 if "USD" in symbol and "BTC" not in symbol else 2)
            mss_price = round(base_price + (atr * 0.4), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            trigger_price = round(base_price + (atr * 0.2), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            fvg_low = round(trigger_price - (fvg_size * 0.5), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            fvg_high = round(trigger_price + (fvg_size * 0.5), 5 if "USD" in symbol and "BTC" not in symbol else 2)
        else:
            sweep_price = round(base_price + sweep_depth, 5 if "USD" in symbol and "BTC" not in symbol else 2)
            mss_price = round(base_price - (atr * 0.4), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            trigger_price = round(base_price - (atr * 0.2), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            fvg_low = round(trigger_price - (fvg_size * 0.5), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            fvg_high = round(trigger_price + (fvg_size * 0.5), 5 if "USD" in symbol and "BTC" not in symbol else 2)
            
        # Calculate a success probability based on feature strength
        # High volume spike, high MSS strength, trend alignment, active session, FVG presence -> High probability
        score = (
            (volume_spike / 3.5) * 0.25 +
            (mss_strength / 3.5) * 0.25 +
            trend_aligned * 0.25 +
            session_strength * 0.15 +
            (1.0 if has_fvg else 0.0) * 0.10
        )
        
        # Map score to probability (say, 30% to 90%)
        success_prob = 0.3 + score * 0.6
        outcome = 1 if random.random() < success_prob else 0
        status = "TP Hit" if outcome == 1 else "SL Hit"
        
        data.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "direction": direction,
            "sweep_price": sweep_price,
            "mss_price": mss_price,
            "trigger_price": trigger_price,
            "sweep_depth": sweep_depth,
            "atr": atr,
            "volume_spike": volume_spike,
            "mss_strength": mss_strength,
            "trend": trend,
            "session": session,
            "fvg_size": fvg_size,
            "fvg_low": fvg_low,
            "fvg_high": fvg_high,
            "status": status,
            "outcome": outcome
        })
        
    return pd.DataFrame(data)

def main():
    print("Generating synthetic TradingView SMC historical dataset...")
    df = generate_synthetic_dataset(250)
    
    # Save dataset to CSV for record
    csv_dir = os.path.join(os.path.dirname(__file__), "../backend/data")
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, "historical_setups.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path} ({len(df)} rows)")
    
    # Train the model using MLEngine
    print("Training XGBoost Classifier using MLEngine...")
    try:
        metrics = ml_engine.train(df)
        print("Training successful!")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        print(f"F1-Score: {metrics['f1_score']:.4f}")
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"Dataset Size: {metrics['dataset_size']}")
        print(f"Saved model: {ml_engine.model_path}")
        print(f"Saved scaler: {ml_engine.scaler_path}")
    except Exception as e:
        print(f"Error training model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
