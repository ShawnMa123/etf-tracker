from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    策略的抽象基类。
    所有具体的策略都必须继承自该类并实现 generate_signals 方法。
    """

    @abstractmethod
    def generate_signals(self, prices_df: pd.DataFrame) -> pd.Series:
        """
        根据历史价格数据生成交易信号。

        :param prices_df: 包含所有资产历史价格的DataFrame。
        :return: 一个以日期为索引的Pandas Series，1代表买入信号，0代表无操作。
                 该Series的索引应覆盖整个回测周期。
        """
        pass