import pandas as pd
from .base import BaseStrategy

class TimeBasedStrategy(BaseStrategy):
    """
    基于固定时间周期的投资策略。
    """
    def __init__(self, frequency: str, day: int):
        """
        :param frequency: 投资频率 ('weekly', 'bi-weekly', 'monthly')
        :param day: 对于 weekly/bi-weekly, 是星期几 (0=周一); 对于 monthly, 是日期.
        """
        self.frequency = frequency.lower()
        self.day = day
        
        if self.frequency not in ['weekly', 'bi-weekly', 'monthly']:
            raise ValueError("频率(frequency)必须是 'weekly', 'bi-weekly', 或 'monthly'")

    def generate_signals(self, prices_df: pd.DataFrame) -> pd.Series:
        # 创建一个覆盖整个价格数据周期的信号序列，并初始化为0
        signals = pd.Series(0, index=prices_df.index)
        
        if self.frequency == 'weekly':
            # 每周的指定星期几买入
            buy_dates = signals.index[signals.index.weekday == self.day]
            signals.loc[buy_dates] = 1
            
        elif self.frequency == 'bi-weekly':
            # 每隔一周的指定星期几买入
            # 找到第一个符合条件的日期
            first_buy_date = None
            for date in signals.index:
                if date.weekday() == self.day:
                    first_buy_date = date
                    break
            
            if first_buy_date:
                # 以第一个购买日为起点，每隔14天标记一次
                date_range = pd.date_range(start=first_buy_date, end=signals.index.max(), freq='14D')
                # 筛选出真实存在的交易日
                buy_dates = signals.index.intersection(date_range)
                signals.loc[buy_dates] = 1

        elif self.frequency == 'monthly':
            # 每月的指定日期买入
            # 我们先标记出所有可能的日历日，后续引擎的顺延逻辑会自动处理非交易日
            date_range_full = pd.date_range(start=signals.index.min(), end=signals.index.max())
            signals_full = pd.Series(0, index=date_range_full)

            for year in range(signals_full.index.min().year, signals_full.index.max().year + 1):
                for month in range(1, 13):
                    try:
                        # 尝试创建指定日期的Timestamp
                        target_date = pd.Timestamp(year=year, month=month, day=self.day)
                        if target_date in signals_full.index:
                            signals_full.loc[target_date] = 1
                    except ValueError:
                        # 如果日期不存在 (如2月30日)，则跳过
                        continue
            
            # 只保留原始交易日索引中的信号
            signals = signals_full[signals.index]

        return signals