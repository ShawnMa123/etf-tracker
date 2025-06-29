import yfinance as yf
import pandas as pd
import os
import pickle

# 定义缓存目录
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_data(tickers, start_date, end_date):
    """
    下载或从缓存加载股票/ETF的价格和股息数据。
    """
    all_data = {}
    price_data = {}
    dividend_data = {}
    
    for ticker in tickers:
        cache_file = os.path.join(CACHE_DIR, f"{ticker}_{start_date}_{end_date}.pkl")
        
        if os.path.exists(cache_file):
            print(f"从缓存加载 {ticker} 的数据...")
            with open(cache_file, 'rb') as f:
                all_data[ticker] = pickle.load(f)
        else:
            print(f"正在下载 {ticker} 的数据...")
            stock = yf.Ticker(ticker)
            # 下载日度数据，确保包含股息和拆股事件
            history = stock.history(start=start_date, end=end_date, auto_adjust=False)
            dividends = stock.dividends
            
            if history.empty:
                print(f"警告: 无法获取 {ticker} 的历史数据。可能会导致错误。")
                continue

            # 保存到缓存
            data_to_cache = {
                'prices': history['Close'],
                'dividends': dividends
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(data_to_cache, f)
            all_data[ticker] = data_to_cache

    # 分离价格和股息数据
    for ticker, data in all_data.items():
        price_data[ticker] = data['prices']
        dividend_data[ticker] = data['dividends']

    # 合并所有价格数据到一个DataFrame，并向前填充缺失值
    prices_df = pd.DataFrame(price_data).ffill().bfill()
    
    # --- FIX START: 统一处理时区问题 ---
    # 检查价格数据的索引是否包含时区信息
    if prices_df.index.tz is not None:
        # 如果有，则移除时区信息，使其变为 tz-naive
        prices_df.index = prices_df.index.tz_localize(None)
        
    # 对股息数据的索引也进行同样的处理
    naive_dividend_data = {}
    for ticker, div_series in dividend_data.items():
        if div_series.index.tz is not None:
            # 移除时区信息
            naive_dividend_data[ticker] = div_series.tz_localize(None)
        else:
            # 如果本来就没有时区信息，直接使用
            naive_dividend_data[ticker] = div_series
    # --- FIX END ---
    
    # 返回处理过的、时区统一的数据
    return prices_df, naive_dividend_data