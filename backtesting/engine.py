import pandas as pd
from .portfolio import Account # 导入我们新创建的 Account 类

def run_backtest(config, prices_df, dividends_data):
    """
    运行回测引擎。
    """
    print("回测引擎启动...")

    # 准备工作
    portfolio_conf = config.PORTFOLIO
    benchmarks_conf = config.BENCHMARKS
    start_date = config.START_DATE
    end_date = config.END_DATE
    investment_amount = config.INVESTMENT_AMOUNT
    investment_day_name = config.INVESTMENT_DAY
    cost_conf = config.TRANSACTION_COST

    day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
    investment_day_num = day_mapping[investment_day_name]

    # 初始化账户 - 使用新的 Account 类
    portfolio_account = Account("Portfolio", tickers=list(portfolio_conf.keys()))
    benchmark_accounts = {bm: Account(bm, tickers=[bm]) for bm in benchmarks_conf}

    # 记录每日数据的列表
    daily_records = []
    
    date_range = pd.date_range(start=start_date, end=end_date)

    for current_date in date_range:
        # --- 1. 处理定投 ---
        if current_date.weekday() == investment_day_num:
            trade_date = current_date
            while trade_date not in prices_df.index and trade_date <= prices_df.index.max():
                trade_date += pd.Timedelta(days=1)
            
            if trade_date in prices_df.index:
                # 投资用户组合
                portfolio_account.add_investment(investment_amount)
                for ticker, weight in portfolio_conf.items():
                    price = prices_df.loc[trade_date, ticker]
                    amount_to_invest = investment_amount * weight
                    cost = _calculate_cost(amount_to_invest, cost_conf)
                    net_investment = amount_to_invest - cost
                    if price > 0:
                        shares_to_buy = net_investment / price
                        portfolio_account.buy(ticker, shares_to_buy)

                # 投资基准
                for bm_name, bm_account in benchmark_accounts.items():
                    bm_account.add_investment(investment_amount)
                    price = prices_df.loc[trade_date, bm_name]
                    cost = _calculate_cost(investment_amount, cost_conf)
                    net_investment = investment_amount - cost
                    if price > 0:
                        shares_to_buy = net_investment / price
                        bm_account.buy(bm_name, shares_to_buy)

        # --- 2. 处理股息再投资 ---
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

        # --- 3. 记录每日快照 ---
        if current_date in prices_df.index:
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