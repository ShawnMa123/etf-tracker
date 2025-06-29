import yfinance as yf
import pandas as pd
import os
import pickle
from utils.price_adjuster import calculate_adjusted_prices # 导入新的工具函数

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_data(tickers, start_date, end_date):
    """
    下载原始价格、股息、拆分数据，并手动计算调整后收盘价。
    这是最可靠的数据处理方式。
    """
    all_adj_prices = {}
    
    for ticker in tickers:
        # 使用新的缓存文件名
        cache_file = os.path.join(CACHE_DIR, f"manual_adj_{ticker}_{start_date}_{end_date}.pkl")
        
        if os.path.exists(cache_file):
            print(f"从缓存加载 {ticker} 的手动调整后价格...")
            with open(cache_file, 'rb') as f:
                all_adj_prices[ticker] = pickle.load(f)
        else:
            print(f"正在下载 {ticker} 的原始数据（价格、股息、拆分）...")
            stock = yf.Ticker(ticker)
            # --- FIX: 使用 auto_adjust=False 并获取 actions ---
            history = stock.history(start=start_date, end=end_date, auto_adjust=False, actions=True)
            
            if history.empty:
                print(f"警告: 无法获取 {ticker} 的历史数据。")
                continue

            # 调用我们的函数来计算调整后价格
            adj_close = calculate_adjusted_prices(
                prices=history['Close'],
                dividends=history['Dividends'],
                splits=history['Stock Splits']
            )
            
            with open(cache_file, 'wb') as f:
                pickle.dump(adj_close, f)
            all_adj_prices[ticker] = adj_close

    if not all_adj_prices:
        raise ValueError("未能加载任何股票数据。")

    prices_df = pd.DataFrame(all_adj_prices).ffill().bfill()
    
    if prices_df.index.tz is not None:
        prices_df.index = prices_df.index.tz_localize(None)
    
    return prices_df