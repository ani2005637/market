import urllib.request
import json
import random
import time
import sys

def send_alert(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            return json.loads(res_data)
    except urllib.error.URLError as e:
        print(f"Error connecting to server: {e}")
        return None

def main():
    url = "http://127.0.0.1:8000/api/signals"
    if len(sys.argv) > 1:
        url = sys.argv[1]
        if not url.startswith("http"):
            url = "https://" + url
        if not url.endswith("/api/signals"):
            url = url.rstrip("/") + "/api/signals"
            
    print(f"Simulating TradingView webhook alerts to {url}...")
    
    # Predefined sample tickers
    symbols = ["BTCUSD", "ETHUSD", "XAUUSD", "EURUSD", "GBPUSD"]
    
    # Generate 5 random signals
    for i in range(5):
        symbol = random.choice(symbols)
        direction = random.choice(["Bullish", "Bearish"])
        
        # Decide trend correlation (60% alignment)
        trend = direction if random.random() < 0.6 else random.choice(["Bullish", "Bearish", "Neutral"])
        session = random.choice(["Asian", "London", "New York"])
        
        # Scale price based on ticker
        if symbol == "BTCUSD":
            base = 65000.0
            atr = 120.0
        elif symbol == "ETHUSD":
            base = 3400.0
            atr = 15.0
        elif symbol == "XAUUSD":
            base = 2330.0
            atr = 12.0
        else: # Forex
            base = 1.0850
            atr = 0.0050
            
        prec = 5 if "USD" in symbol and symbol not in ["BTCUSD", "ETHUSD"] else 2
        
        volume_spike = round(random.uniform(0.8, 3.2), 2)
        mss_strength = round(random.uniform(0.8, 3.2), 2)
        sweep_depth = round(atr * random.uniform(0.1, 0.4), prec)
        fvg_size = round(atr * random.uniform(0.15, 0.5), prec)
        
        if direction == "Bullish":
            trigger_price = round(base + (atr * 0.1), prec)
            sweep_price = round(base - sweep_depth, prec)
            mss_price = round(base + (atr * 0.35), prec)
            fvg_low = round(trigger_price - (fvg_size * 0.5), prec)
            fvg_high = round(trigger_price + (fvg_size * 0.5), prec)
        else:
            trigger_price = round(base - (atr * 0.1), prec)
            sweep_price = round(base + sweep_depth, prec)
            mss_price = round(base - (atr * 0.35), prec)
            fvg_low = round(trigger_price - (fvg_size * 0.5), prec)
            fvg_high = round(trigger_price + (fvg_size * 0.5), prec)
            
        payload = {
            "symbol": symbol,
            "timeframe": random.choice(["5m", "15m", "1h"]),
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
            "fvg_high": fvg_high
        }
        
        print(f"\nSending alert {i+1}/5:")
        print(f"  Ticker: {symbol} | Type: {direction} | Trigger: {trigger_price}")
        print(f"  Vol Spike: {volume_spike} | MSS Str: {mss_strength} | Trend: {trend} | Session: {session}")
        
        res = send_alert(url, payload)
        if res:
            print(f"  --> [SUCCESS] Logged in DB as Signal ID: {res['id']}")
            print(f"  --> Setup Score: {res['setup_score']}/10 | ML Win Probability: {res['probability_score']}%")
        else:
            print("  --> [FAILED] Could not send signal alert. Is the FastAPI server running?")
            
        time.sleep(1)

if __name__ == "__main__":
    main()
