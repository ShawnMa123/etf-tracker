import pandas as pd
from .portfolio import Account

def run_backtest(config, prices_df, signals):
    """
    运行回测引擎。
    由于使用调整后收盘价，不再需要手动处理股息。
    """
    print("回测引擎启动...")

    portfolio_conf = config.PORTFOLIO
    investment_amount = config.INVESTMENT_AMOUNT
    cost_conf = config.TRANSACTION_COST

    portfolio_account = Account("Portfolio", tickers=list(portfolio_conf.keys()))
    benchmark_accounts = {bm: Account(bm, tickers=[bm]) for bm in config.BENCHMARKS}

    daily_records = []
    
    for current_date in prices_df.index:
        # --- 1. 检查并执行买入信号 ---
        if signals.get(current_date, 0) == 1:
            # 投资用户组合
            portfolio_account.add_investment(investment_amount)
            for ticker, weight in portfolio_conf.items():
                price = prices_df.loc[current_date, ticker]
                amount_to_invest = investment_amount * weight
                cost = _calculate_cost(amount_to_invest, cost_conf)
                net_investment = amount_to_invest - cost
                if price > 0:
                    shares_to_buy = net_investment / price
                    portfolio_account.buy(ticker, shares_to_buy)

            # 投资基准
            for bm_name, bm_account in benchmark_accounts.items():
                bm_account.add_investment(investment_amount)
                price = prices_df.loc[current_date, bm_name]
                cost = _calculate_cost(investment_amount, cost_conf)
                net_investment = investment_amount - cost
                if price > 0:
                    shares_to_buy = net_investment / price
                    bm_account.buy(bm_name, shares_to_buy)

        # --- 2. 股息处理部分被移除 ---
        # 调整后收盘价已经包含了股息收益，无需手动再投资。

        # --- 3. 记录每日快照 ---
        current_day_prices = prices_df.loc[current_date]
        
        record = {
            'Date': current_date,
            'Portfolio_Value': portfolio_account.get_market_value(current_day_prices),
            'Total_Invested': portfolio_account.total_invested
        }
        
        for bm_name, bm_account in benchmark_accounts.items():
            record[f'{bm_name}_Value'] = bm_account.get_market_value(current_day_prices)
            
        daily_records.append(record)

    print("回测引擎完成。")
    return pd.DataFrame(daily_records).set_index('Date')

def _calculate_cost(amount, cost_conf):
    if cost_conf['type'] == 'fixed':
        return cost_conf['value']
    elif cost_conf['type'] == 'percentage':
        return amount * cost_conf['value']
    return 0.0