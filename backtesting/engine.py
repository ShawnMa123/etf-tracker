import pandas as pd

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

    # 将星期名转换为数字 (Monday=0, Sunday=6)
    day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
    investment_day_num = day_mapping[investment_day_name]

    # 初始化账户
    # 用户投资组合账户
    portfolio_shares = {ticker: 0.0 for ticker in portfolio_conf.keys()}
    
    # 基准账户
    benchmark_shares = {bm: 0.0 for bm in benchmarks_conf}

    # 记录每日数据的列表
    daily_records = []
    total_invested_capital = 0.0

    # 生成回测日期范围
    date_range = pd.date_range(start=start_date, end=end_date)

    for current_date in date_range:
        # --- 1. 处理定投 ---
        if current_date.weekday() == investment_day_num:
            # 寻找实际交易日（如果当天非交易日，则顺延）
            trade_date = current_date
            while trade_date not in prices_df.index and trade_date <= prices_df.index.max():
                trade_date += pd.Timedelta(days=1)
            
            if trade_date in prices_df.index:
                total_invested_capital += investment_amount
                
                # 投资用户组合
                for ticker, weight in portfolio_conf.items():
                    price = prices_df.loc[trade_date, ticker]
                    amount_to_invest = investment_amount * weight
                    cost = _calculate_cost(amount_to_invest, cost_conf)
                    net_investment = amount_to_invest - cost
                    if price > 0:
                        portfolio_shares[ticker] += net_investment / price

                # 投资基准
                for bm in benchmarks_conf:
                    price = prices_df.loc[trade_date, bm]
                    cost = _calculate_cost(investment_amount, cost_conf)
                    net_investment = investment_amount - cost
                    if price > 0:
                        benchmark_shares[bm] += net_investment / price

        # --- 2. 处理股息再投资 ---
        all_holdings = {**portfolio_shares, **benchmark_shares}
        for ticker, shares in all_holdings.items():
            if shares > 0 and ticker in dividends_data and current_date in dividends_data[ticker].index:
                dividend_per_share = dividends_data[ticker][current_date]
                total_dividend = shares * dividend_per_share
                
                price = prices_df.loc[current_date, ticker]
                if price > 0:
                    reinvest_shares = total_dividend / price
                    if ticker in portfolio_shares:
                        portfolio_shares[ticker] += reinvest_shares
                    if ticker in benchmark_shares:
                        benchmark_shares[ticker] += reinvest_shares

        # --- 3. 记录每日快照 ---
        if current_date in prices_df.index:
            # 计算用户组合市值
            portfolio_value = sum(portfolio_shares[t] * prices_df.loc[current_date, t] for t in portfolio_conf.keys())
            
            # 计算基准市值
            benchmark_values = {bm: benchmark_shares[bm] * prices_df.loc[current_date, bm] for bm in benchmarks_conf}
            
            record = {
                'Date': current_date,
                'Portfolio_Value': portfolio_value,
                'Total_Invested': total_invested_capital
            }
            record.update({f'{bm}_Value': val for bm, val in benchmark_values.items()})
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