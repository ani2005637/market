import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from backend.config import settings

# Attempt to import ML libraries; handle import errors if packages aren't fully installed yet
try:
    from xgboost import XGBClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import RobustScaler
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

class MLEngine:
    def __init__(self):
        self.model_path = os.path.join(settings.MODEL_DIR, settings.MODEL_NAME)
        self.scaler_path = os.path.join(settings.MODEL_DIR, settings.SCALER_NAME)
        self.model = None
        self.scaler = None
        self.load_model()
        
    def load_model(self) -> bool:
        """Loads the serialized XGBoost model and scaler from disk."""
        if not ML_AVAILABLE:
            return False
        
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False

    def calculate_setup_score(self, data: Dict[str, Any]) -> float:
        """
        Calculates a deterministic rule-based setup score between 0 and 10.
        This serves as the educational 'setup_score' metric.
        """
        score = 0.0
        
        # 1. Volume Spike (Max 2.5 pts)
        vol_spike = data.get("volume_spike", 1.0)
        if vol_spike >= 2.0:
            score += 2.5
        elif vol_spike >= 1.5:
            score += 2.0
        elif vol_spike >= 1.0:
            score += 1.0
            
        # 2. MSS Strength (Max 2.5 pts)
        mss_str = data.get("mss_strength", 1.0)
        if mss_str >= 2.0:
            score += 2.5
        elif mss_str >= 1.5:
            score += 2.0
        elif mss_str >= 1.0:
            score += 1.0
            
        # 3. FVG Presence & Size (Max 2.0 pts)
        fvg_size = data.get("fvg_size", 0.0)
        atr = data.get("atr", 1.0)
        if fvg_size and atr > 0:
            fvg_ratio = fvg_size / atr
            if fvg_ratio >= 0.5:
                score += 2.0
            else:
                score += 1.0
                
        # 4. Trend Alignment (Max 2.0 pts)
        trend = data.get("trend", "Neutral")
        direction = data.get("direction", "Bullish")
        if trend == direction:
            score += 2.0
        elif trend == "Neutral":
            score += 1.0
            
        # 5. Trading Session (Max 1.0 pt)
        session = data.get("session", "Asian")
        if session in ["London", "New York"]:
            score += 1.0
        else:
            score += 0.5
            
        return min(round(score, 2), 10.0)

    def extract_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Preprocesses raw alert data into numeric feature values.
        """
        # Direction mapping: Bullish -> 1, Bearish -> 0
        direction_val = 1.0 if data.get("direction") == "Bullish" else 0.0
        
        # Trend mapping: Bullish -> 2, Neutral -> 1, Bearish -> 0
        trend_str = data.get("trend", "Neutral")
        trend_val = 1.0
        if trend_str == "Bullish":
            trend_val = 2.0
        elif trend_str == "Bearish":
            trend_val = 0.0
            
        # Session mapping: Asian -> 0, London -> 1, New York -> 2
        session_str = data.get("session", "Asian")
        session_val = 0.0
        if session_str == "London":
            session_val = 1.0
        elif session_str == "New York":
            session_val = 2.0
            
        atr = data.get("atr", 1.0)
        atr = atr if atr > 0 else 1.0
        
        sweep_depth = data.get("sweep_depth", 0.0)
        sweep_depth_atr_ratio = sweep_depth / atr
        
        fvg_size = data.get("fvg_size", 0.0) or 0.0
        fvg_size_atr_ratio = fvg_size / atr
        
        return {
            "direction_encoded": direction_val,
            "trend_encoded": trend_val,
            "session_encoded": session_val,
            "sweep_depth_atr_ratio": sweep_depth_atr_ratio,
            "volume_spike": float(data.get("volume_spike", 1.0)),
            "mss_strength": float(data.get("mss_strength", 1.0)),
            "fvg_size_atr_ratio": fvg_size_atr_ratio,
            "atr": float(atr)
        }

    def predict_probability(self, data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Returns (probability_score, setup_score).
        Falls back to rule-based scores if ML is unavailable.
        """
        setup_score = self.calculate_setup_score(data)
        
        # Default probability is derived from setup score if ML is unavailable
        default_prob = float(setup_score * 10.0)
        
        if not ML_AVAILABLE or self.model is None or self.scaler is None:
            # Add a slight variation based on trend/session to make default dynamic
            mod = 0.0
            if data.get("session") in ["London", "New York"]:
                mod += 3.0
            if data.get("trend") == data.get("direction"):
                mod += 5.0
            prob = min(max(default_prob + mod, 10.0), 95.0)
            return round(prob, 1), setup_score

        try:
            features_dict = self.extract_features(data)
            features_df = pd.DataFrame([features_dict])
            
            # Ensure column order matches training
            columns = [
                "direction_encoded", "trend_encoded", "session_encoded", 
                "sweep_depth_atr_ratio", "volume_spike", "mss_strength", 
                "fvg_size_atr_ratio", "atr"
            ]
            features_df = features_df[columns]
            
            # Scale features
            scaled_features = self.scaler.transform(features_df)
            
            # Predict probability
            prob_arr = self.model.predict_proba(scaled_features)
            # Probability of target class 1 (TP Hit / Success)
            prob = float(prob_arr[0][1] * 100.0)
            return round(prob, 1), setup_score
        except Exception as e:
            print(f"Error predicting probability: {e}")
            return round(default_prob, 1), setup_score

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains a new XGBoost classifier and saves the model.
        Expects a pandas DataFrame containing raw feature columns and target 'outcome'.
        """
        if not ML_AVAILABLE:
            raise RuntimeError("Scikit-learn and XGBoost libraries are not installed or imported.")
            
        if len(df) < 10:
            raise ValueError(f"Insufficient training data. Minimum 10 samples required, got {len(df)}")
            
        # 1. Feature Extraction
        feature_list = []
        for _, row in df.iterrows():
            feat = self.extract_features(row.to_dict())
            feat["outcome"] = int(row["outcome"])
            feature_list.append(feat)
            
        processed_df = pd.DataFrame(feature_list)
        
        X = processed_df.drop(columns=["outcome"])
        y = processed_df["outcome"]
        
        # Ensure column order
        columns = [
            "direction_encoded", "trend_encoded", "session_encoded", 
            "sweep_depth_atr_ratio", "volume_spike", "mss_strength", 
            "fvg_size_atr_ratio", "atr"
        ]
        X = X[columns]
        
        # 2. Train/Test Split
        # Handle small datasets by reducing test size or disabling split if extremely small
        test_size = 0.2 if len(X) >= 20 else 0.1
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        
        # 3. Fit Scaler
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 4. Train Model
        model = XGBClassifier(
            n_estimators=50 if len(X) < 100 else 150,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )
        model.fit(X_train_scaled, y_train)
        
        # 5. Evaluate
        preds = model.predict(X_test_scaled)
        probs = model.predict_proba(X_test_scaled)[:, 1]
        
        accuracy = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        try:
            roc_auc = float(roc_auc_score(y_test, probs))
        except Exception:
            roc_auc = 0.5 # Fallback if ROC AUC can't be calculated (e.g. single class in test set)
            
        # 6. Save Model
        joblib.dump(model, self.model_path)
        joblib.dump(scaler, self.scaler_path)
        
        # Update current instances
        self.model = model
        self.scaler = scaler
        
        return {
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "dataset_size": len(df)
        }

ml_engine = MLEngine()
