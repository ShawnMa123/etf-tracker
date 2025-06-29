# --- 投资组合与基准配置 ---
PORTFOLIO = {
    'QQQ': 0.9,
    'TSLA': 0.1
}
BENCHMARKS = ['SPY', 'DIA', 'QQQ']

# --- 回测周期配置 ---
START_DATE = '2014-01-01'
END_DATE = '2024-01-01'

# --- 通用投资参数 ---
# 对于所有策略，当触发买入信号时，投入的固定金额
INVESTMENT_AMOUNT = 100.00

# --- 交易成本配置 ---
TRANSACTION_COST = {
    'type': 'fixed',
    'value': 0.25 
}

# --- 策略选择与配置 ---
# 用户在这里选择并配置他们想要的策略。取消注释你想要使用的策略。

# === 策略示例 1: 每周三定投 ===
# STRATEGY_CONFIG = {
#     'type': 'time_based',
#     'frequency': 'weekly',   # 可选: 'weekly', 'bi-weekly', 'monthly'
#     'day': 2,                # 对于 weekly/bi-weekly, 0=周一...; 对于 monthly, 是日期 1-31
# }

# # === 策略示例 2: 双周周二定投 ===
# STRATEGY_CONFIG = {
#     'type': 'time_based',
#     'frequency': 'bi-weekly',
#     'day': 1,
# }

# # === 策略示例 3: 每月15号定投 ===
# STRATEGY_CONFIG = {
#     'type': 'time_based',
#     'frequency': 'monthly',
#     'day': 15,
# }

# # === 策略示例 4: SPY的50/200日均线金叉策略 ===
STRATEGY_CONFIG = {
    'type': 'sma_crossover',
    'ticker_for_signal': 'SPY',
    'short_window': 50,
    'long_window': 200,
}
