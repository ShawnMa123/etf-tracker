# --- 投资组合与基准配置 ---
# 定义您的投资组合及其权重。权重之和应为 1.0。
PORTFOLIO = {
    'QQQ': 0.9,
    'TSLA': 0.1
}

# 定义用于比较的基准ETF
BENCHMARKS = ['SPY', 'DIA', 'QQQ']

# --- 回测周期配置 ---
START_DATE = '2014-01-01'
END_DATE = '2024-01-01'

# --- 投资策略配置 ---
# 每周投资金额
INVESTMENT_AMOUNT = 100.00  # 使用浮点数以保证精度

# 选择定投日: 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'
INVESTMENT_DAY = 'Wednesday'

# --- 交易成本配置 ---
# 'type': 'fixed' (固定金额) 或 'percentage' (百分比)
# 'value': 如果是 fixed，直接写金额；如果是 percentage，写小数 (例如 0.05% 就是 0.0005)
TRANSACTION_COST = {
    'type': 'fixed',
    'value': 0.25 
}
# 如果不想计算交易成本，可以设置为:
# TRANSACTION_COST = {'type': 'fixed', 'value': 0.0}