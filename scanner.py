import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json

# 1. CONFIGURATION
# Yahoo Finance Ticker Guide:
# - Crypto: Add "-USD" (e.g., "BTC-USD", "PEPE-USD", "WIF-USD")
# - Stocks: Just the symbol (e.g., "TSLA", "NVDA", "GME")

ASSETS = [
    # --- CRYPTO ---
    'BTC-USD',      # Bitcoin
    'ETH-USD',      # Ethereum
    'SOL-USD',      # Solana
    'PEPE-USD',     # Pepe
    'WIF-USD',      # Dogwifhat
    'DOGE-USD',     # Dogecoin
    'XRP-USD',      # Ripple

    # --- STOCKS ---
    'NVDA',         # Nvidia
    'TSLA',         # Tesla
    'MSTR',         # MicroStrategy
    'COIN',         # Coinbase
    'AAPL',         # Apple
    'AMD',          # AMD
]

TIMEFRAME = '1d'  # Daily candles
SUPERTREND_LENGTH = 10
SUPERTREND_FACTOR = 3.0

def get_supertrend_signal(ticker):
    try:
        # Fetch historical data
        df = yf.download(ticker, period="3mo", interval=TIMEFRAME, progress=False)
        
        if df.empty:
            return None

        # Calculate SuperTrend
        st = df.ta.supertrend(length=SUPERTREND_LENGTH, multiplier=SUPERTREND_FACTOR)
        
        # Identify the direction column (1 = Bullish, -1 = Bearish)
        # pandas_ta names columns like 'SUPERTd_10_3.0'
        st_dir_col = f'SUPERTd_{SUPERTREND_LENGTH}_{SUPERTREND_FACTOR}'
        
        # Join the SuperTrend data to the main dataframe
        df = df.join(st)
        
        # Get latest values
        current_price = df['Close'].iloc[-1]
        current_trend = df[st_dir_col].iloc[-1] 
        
        # FIND THE FLIP DATE
        # We loop backwards to find when the trend changed
        days_since_flip = 0
        price_at_flip = current_price
        
        # 1 = Bullish (Green), -1 = Bearish (Red)
        target_trend = current_trend
        
        for i in range(len(df)-2, 0, -1):
            if df[st_dir_col].iloc[i] != target_trend:
                # Found the flip!
                # The flip actually happened on the candle at index i+1
                price_at_flip = df['Close'].iloc[i+1]
                days_since_flip = len(df) - 1 - (i+1)
                break
        
        # Format Data
        trend_label = "BULLISH" if current_trend == 1 else "BEARISH"
        
        # Handle cases where price_at_flip might be zero to avoid division error
        if price_at_flip == 0: price_at_flip = current_price
            
        pct_change = ((current_price - price_at_flip) / price_at_flip) * 100
        
        return {
            "token": ticker.replace("-USD", ""), # Clean name
            "trend": trend_label,
            "pct_change": round(pct_change, 2),
            "days_since_flip": days_since_flip,
            "price": round(float(current_price), 2)
        }

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

# 2. RUN ANALYSIS
print("Fetching market data...")
dashboard_data = []

for asset in ASSETS:
    data = get_supertrend_signal(asset)
    if data:
        dashboard_data.append(data)

# 3. SAVE DATA
# We write this to a JS file so the HTML can read it easily
with open('dashboard_data.js', 'w') as f:
    f.write(f"const stockData = {json.dumps(dashboard_data, indent=4)};")

print("Done! Data saved to dashboard_data.js")
