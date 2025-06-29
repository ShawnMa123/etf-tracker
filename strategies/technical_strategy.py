import pandas as pd
from .base import BaseStrategy

class SMACrossoverStrategy(BaseStrategy):
    """
    简单移动平均线 (SMA) 交叉策略。
    """
    def __init__(self, ticker_for_signal: str, short_window: int, long_window: int):
        self.ticker = ticker_for_signal
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, prices_df: pd.DataFrame) -> pd.Series:
        if self.ticker not in prices_df.columns:
            raise ValueError(f"用于生成信号的标的'{self.ticker}'不在价格数据中。")

        signals = pd.Series(0, index=prices_df.index)
        
        # 计算短期和长期SMA
        short_sma = prices_df[self.ticker].rolling(window=self.short_window, min_periods=1).mean()
        long_sma = prices_df[self.ticker].rolling(window=self.long_window, min_periods=1).mean()

        # 生成一个布尔序列：当短期线上穿长期线时为True
        # 我们用 .diff() > 0 来捕捉“上穿”的瞬间，而不是持续在上方
        # 但根据用户要求“只要满足条件，每周都买”，我们先标记所有金叉状态
        golden_cross_status = short_sma > long_sma

        # 根据规则“每周最多买一次”进行处理
        # 我们将每日的状态重采样到每周，并取每周的最后一个状态
        # 如果一周的最后一天是金叉状态，我们就认为这周可以买
        weekly_buy_signal = golden_cross_status.resample('W').last()

        # 找到那些需要买入的周
        weeks_to_buy = weekly_buy_signal[weekly_buy_signal].index

        # 在每周的开始（通常是周一）生成买入信号
        for week_end_date in weeks_to_buy:
            # 找到该周的开始日期
            start_of_week = week_end_date - pd.Timedelta(days=6)
            # 找到该周在我们的交易日历中的第一个交易日
            buy_date_candidate = prices_df.index[(prices_df.index >= start_of_week) & (prices_df.index <= week_end_date)]
            if not buy_date_candidate.empty:
                # 在第一个交易日设置买入信号
                signals.loc[buy_date_candidate[0]] = 1
                
        return signals