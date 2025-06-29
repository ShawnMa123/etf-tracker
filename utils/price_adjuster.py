import pandas as pd

def calculate_adjusted_prices(prices: pd.Series, dividends: pd.Series, splits: pd.Series) -> pd.Series:
    """
    根据原始收盘价、股息和拆分数据，从后向前计算调整后收盘价。
    
    :param prices: 原始收盘价序列
    :param dividends: 股息序列
    :param splits: 股票拆分序列
    :return: 调整后收盘价序列
    """
    # 复制价格序列，避免修改原始数据
    adj_prices = prices.copy()

    # 从后向前遍历日期
    for i in range(len(adj_prices) - 2, -1, -1):
        # 当前日期和前一天的日期
        today = adj_prices.index[i]
        prev_day = adj_prices.index[i+1]
        
        # 继承前一天的调整后价格
        adj_prices.iloc[i] = adj_prices.iloc[i+1]

        # 检查在前一天是否有拆分事件
        if prev_day in splits.index and splits[prev_day] != 0:
            split_ratio = splits[prev_day]
            adj_prices.iloc[i] /= split_ratio
        
        # 检查在前一天是否有股息事件
        if prev_day in dividends.index and dividends[prev_day] != 0:
            dividend = dividends[prev_day]
            # 用“今天”的原始价格来计算调整因子
            # 这是因为除息日的股价下跌是基于当天的价格
            price_on_ex_div = prices.loc[today]
            adj_prices.iloc[i] *= (1 - dividend / price_on_ex_div)

    # 将调整后的序列与原始价格序列的比例应用到整个序列
    # 这确保了调整后的价格与原始价格的相对关系是正确的
    ratio = adj_prices / prices
    return prices * ratio.iloc[-1]