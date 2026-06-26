# Smart Liquidity AI MVP

Smart Liquidity AI is a TradingView-compatible trading intelligence system that combines **Smart Money Concepts (SMC)** with **Machine Learning (XGBoost)** to score and evaluate trading setups in real-time.

Built for **Sanna Innovations**, this system automatically detects Liquidity Sweeps, Market Structure Shifts (MSS), and Fair Value Gaps (FVG) on charts, sends them via webhook to a FastAPI backend, scores them using an XGBoost classifier, and visualizes active setups on a premium dark glassmorphic web dashboard.

---

## 🚀 Key Features

* **Advanced SMC Detection**: Detects Swing Highs/Lows, Liquidity Levels, Liquidity Sweeps, Market Structure Shifts (MSS), and Fair Value Gaps (FVGs) using Pine Script v6.
* **XGBoost Machine Learning Classifier**: Extracts engineered features (volume spikes, MSS candle strength, sweep depth, FVG size ratio relative to ATR) and predicts setup success probability (TP Hit before SL Hit).
* **Rule-Based Baseline Scorer**: A deterministic 0-10 scoring engine functioning as a baseline and educational indicator.
* **Vibrant Glassmorphic Dashboard**: A web interface featuring dark-mode gradients, active setups tracking, win-rate stats, manual tagging, and an interactive TradingView webhook simulator.
* **SQLite / PostgreSQL Compatible**: Defaults to SQLite for local development, easily configurable for PostgreSQL in production.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── data/                   # Labeled historical setups database
│   ├── ml/
│   │   └── engine.py           # ML Model preprocessing, training, & prediction
│   ├── static/                 # Glassmorphic Frontend (HTML, CSS, JS)
│   ├── config.py               # Application configurations (JWT, paths, etc.)
│   ├── db.py                   # SQLAlchemy connection session
│   ├── main.py                 # FastAPI Application routes & webhooks
│   ├── models.py               # Database schemas (User, Signal, MLModelStatus)
│   ├── schemas.py              # Pydantic validation schemas
│   └── requirements.txt        # Python backend package dependencies
├── tradingview/
│   └── smart_liquidity_indicator.pine  # Pine Script v6 TradingView indicator
├── scripts/
│   ├── generate_synthetic_data.py      # Synthetic setups generation & ML pre-training
│   └── simulate_webhook.py             # Script to simulate TradingView webhook calls
└── README.md
```

---

## 🛠️ Setup & Installation

### Prerequisites
* Python 3.10 or higher.
* Git (to clone and push).

### Step 1: Clone the Repository & Navigate
```bash
git clone <your-repository-url>
cd <repository-folder>
```

### Step 2: Create and Activate a Python Virtual Environment
**On Windows:**
```powershell
python -m venv backend/venv
.\backend\venv\Scripts\activate
```
**On macOS/Linux:**
```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
```

### Step 3: Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Pre-train the XGBoost Model
Generate a synthetic historical dataset of 250 setups and train the baseline XGBoost model:
```bash
python scripts/generate_synthetic_data.py
```
This saves `xgboost_setup_classifier.joblib` and `robust_scaler.joblib` into the `ml_models/` directory.

### Step 5: Start the FastAPI Server
Run the application locally:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
The server is now live at **`http://127.0.0.1:8000`**.

---

## 📊 Dashboard Usage & Verification

1. Open your browser and navigate to **`http://127.0.0.1:8000/`**.
2. **Simulate Webhooks**: Use the **TradingView Webhook Simulator** panel on the left to inject simulated setups and verify they populate the table, compute probabilities, and update statistics.
3. **Verify via Script**: Alternatively, open a new terminal and run:
   ```bash
   python scripts/simulate_webhook.py
   ```
4. **Admin Features**:
   * Click **Admin Login** in the top right.
   * Credentials: **`admin`** / **`admin123`**
   * Tag pending setups as **TP** or **SL** to create new training data.
   * Navigate to **ML Engine Control** to trigger model retraining.

---

## 📈 TradingView Integration

1. Open a chart on TradingView.
2. Open the **Pine Editor** at the bottom, paste the code from [smart_liquidity_indicator.pine](tradingview/smart_liquidity_indicator.pine), and click **Add to Chart**.
3. Create an alert on the indicator:
   * **Condition**: Select `Smart Liquidity AI SMC Engine (v6)`.
   * **Action**: Check `Webhook URL` and enter your public server URL: `http://<your-public-ip>:8000/api/signals`.
   * **Message**: Paste the following placeholder (the indicator auto-populates it):
     ```json
     {{plot("Bullish Sweep") or plot("Bearish Sweep") or plot("Bullish MSS") or plot("Bearish MSS")}}
     ```

---

## 🔒 Security & Deployment Notes

* **Production Deployment**: Use Docker and deploy behind an Nginx reverse proxy using HTTPS.
* **Production Database**: Replace SQLite with PostgreSQL by setting the `DATABASE_URL` environment variable:
  ```bash
  DATABASE_URL="postgresql://user:password@host:5432/dbname"
  ```
* **JWT Secret**: Change the default `SECRET_KEY` in `backend/config.py` (or set via environment variable) to secure admin endpoints.

---

## ⚠️ Disclaimer
This tool is for educational and research purposes only. It does not constitute investment advice or guarantee trading profits. Use at your own risk.
