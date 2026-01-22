import yfinance as yf
import pandas as pd
import numpy as np
import json

# 1. CONFIGURATION
ASSETS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'PEPE-USD', 'WIF-USD',
    'NVDA', 'TSLA', 'MSTR', 'COIN', 'AAPL', 'AMD'
]
TIMEFRAME = '1d'
ATR_PERIOD = 10
FACTOR = 3.0

def calculate_supertrend(df, period=10, multiplier=3):
    # Manual SuperTrend Calculation (No pandas_ta needed!)
    hl2 = (df['High'] + df['Low']) / 2
    
    # Calculate ATR
    df['tr0'] = abs(df['High'] - df['Low'])
    df['tr1'] = abs(df['High'] - df['Close'].shift())
    df['tr2'] = abs(df['Low'] - df['Close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    
    # Basic Bands
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['in_uptrend'] = True
    
    for current in range(1, len(df.index)):
        previous = current - 1
        
        if df['Close'][current] > df['upperband'][previous]:
            df.loc[df.index[current], 'in_uptrend'] = True
        elif df['Close'][current] < df['lowerband'][previous]:
            df.loc[df.index[current], 'in_uptrend'] = False
        else:
            df.loc[df.index[current], 'in_uptrend'] = df['in_uptrend'][previous]
            
            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df.loc[df.index[current], 'lowerband'] = df['lowerband'][previous]
            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df.loc[df.index[current], 'upperband'] = df['upperband'][previous]
                
    return df

def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval=TIMEFRAME, progress=False)
        if df.empty: return None
        
        # Flatten columns if multi-index (common yfinance issue)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Run Manual Math
        df = calculate_supertrend(df, ATR_PERIOD, FACTOR)
        
        # Get Latest Data
        current_trend = "BULLISH" if df['in_uptrend'].iloc[-1] else "BEARISH"
        current_price = df['Close'].iloc[-1]
        
        # Find Flip
        days_since = 0
        price_at_flip = current_price
        target_state = df['in_uptrend'].iloc[-1]
        
        for i in range(len(df)-2, 0, -1):
            if df['in_uptrend'].iloc[i] != target_state:
                price_at_flip = df['Close'].iloc[i+1]
                days_since = len(df) - 1 - (i+1)
                break
                
        pct_change = ((current_price - price_at_flip) / price_at_flip) * 100
        
        return {
            "token": ticker.replace("-USD", ""),
            "trend": current_trend,
            "pct_change": round(pct_change, 2),
            "days_since_flip": days_since,
            "price": round(float(current_price), 2)
        }
    except Exception as e:
        print(f"Skipping {ticker}: {e}")
        return None

# 2. RUN ANALYSIS
print("Fetching market data...")
data_list = []
for asset in ASSETS:
    result = analyze_asset(asset)
    if result: data_list.append(result)

# 3. SAVE
with open('dashboard_data.js', 'w') as f:
    f.write(f"const stockData = {json.dumps(data_list, indent=4)};")
print("Done!")
