from .base import BaseStrategy
from .time_strategy import TimeBasedStrategy
from .technical_strategy import SMACrossoverStrategy

def create_strategy(strategy_config: dict) -> BaseStrategy:
    """
    策略工厂，根据配置创建并返回一个策略实例。
    """
    strategy_type = strategy_config.get('type')
    
    if strategy_type == 'time_based':
        return TimeBasedStrategy(
            frequency=strategy_config['frequency'],
            day=strategy_config['day']
        )
    elif strategy_type == 'sma_crossover':
        return SMACrossoverStrategy(
            ticker_for_signal=strategy_config['ticker_for_signal'],
            short_window=strategy_config['short_window'],
            long_window=strategy_config['long_window']
        )
    else:
        raise ValueError(f"未知的策略类型: '{strategy_type}'")