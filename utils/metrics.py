import pandas as pd
import numpy as np

def calculate_cagr(end_value, start_value, years):
    """计算年化复合增长率 (CAGR)"""
    if start_value == 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / years) - 1

def calculate_max_drawdown(series):
    """计算最大回撤"""
    # 使用累积最大值计算每个时间点的回撤
    cumulative_max = series.cummax()
    drawdown = (series - cumulative_max) / cumulative_max
    
    # 获取最大回撤值（最小的负数）
    max_drawdown_value = drawdown.min()
    
    return max_drawdown_value if not pd.isna(max_drawdown_value) else 0.0