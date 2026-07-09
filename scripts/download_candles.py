import ccxt
import pandas as pd
import time
import os

def download_data():
    symbol = "BTC/USDT"
    timeframe = "30m"
    exchange = ccxt.binance({"enableRateLimit": True})
    
    # 1 year ago in ms
    now_ms = int(time.time() * 1000)
    one_year_ms = 365 * 24 * 60 * 60 * 1000
    start_time = now_ms - one_year_ms
    
    print(f"Downloading 30m historical data for {symbol} starting from 1 year ago...")
    
    all_candles = []
    since = start_time
    
    while since < now_ms:
        try:
            print(f"Fetching candles since {pd.to_datetime(since, unit='ms')}...")
            candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if not candles:
                break
            all_candles.extend(candles)
            since = candles[-1][0] + 30 * 60 * 1000
            time.sleep(0.2)
        except Exception as e:
            print(f"Error fetching: {e}. Retrying in 2 seconds...")
            time.sleep(2)
            
    if not all_candles:
        print("No candles fetched!")
        return
        
    df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    
    output_path = "btc_30m_1y.csv"
    df.to_csv(output_path, index=False)
    print(f"Success! Downloaded {len(df)} candles and saved to {output_path}")

if __name__ == "__main__":
    download_data()
