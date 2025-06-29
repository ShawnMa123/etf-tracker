import pandas as pd
from .portfolio import Account

def run_backtest(config, prices_df, dividends_data, signals):
    """
    运行回测引擎。
    现在接收一个 signals 参数，而不是自己计算投资日。
    """
    print("回测引擎启动...")

    portfolio_conf = config.PORTFOLIO
    investment_amount = config.INVESTMENT_AMOUNT
    cost_conf = config.TRANSACTION_COST

    # 初始化账户
    portfolio_account = Account("Portfolio", tickers=list(portfolio_conf.keys()))
    benchmark_accounts = {bm: Account(bm, tickers=[bm]) for bm in config.BENCHMARKS}

    # 记录每日数据的列表
    daily_records = []
    
    # 引擎现在使用价格数据的索引作为其循环基准
    for current_date in prices_df.index:
        # --- 1. 检查并执行买入信号 ---
        # 使用 .get() 安全地访问信号，如果某天不在信号序列中，则默认为0
        if signals.get(current_date, 0) == 1:
            # 购买逻辑现在只在这里触发
            
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

            # 投资基准 (基准也使用相同的信号进行定投，以作公平比较)
            for bm_name, bm_account in benchmark_accounts.items():
                bm_account.add_investment(investment_amount)
                price = prices_df.loc[current_date, bm_name]
                cost = _calculate_cost(investment_amount, cost_conf)
                net_investment = investment_amount - cost
                if price > 0:
                    shares_to_buy = net_investment / price
                    bm_account.buy(bm_name, shares_to_buy)

        # --- 2. 处理股息再投资 (逻辑不变) ---
        all_accounts = [portfolio_account] + list(benchmark_accounts.values())
        for account in all_accounts:
            for ticker, shares in account.shares.items():
                if shares > 0 and ticker in dividends_data and current_date in dividends_data[ticker].index:
                    dividend_per_share = dividends_data[ticker][current_date]
                    total_dividend = shares * dividend_per_share
                    price = prices_df.loc[current_date, ticker]
                    if price > 0:
                        reinvest_shares = total_dividend / price
                        account.buy(ticker, reinvest_shares)

        # --- 3. 记录每日快照 (逻辑不变) ---
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
    """计算单笔交易成本"""
    if cost_conf['type'] == 'fixed':
        return cost_conf['value']
    elif cost_conf['type'] == 'percentage':
        return amount * cost_conf['value']
    return 0.0