import pandas as pd
import config
from data import loader
from backtesting import engine
from reporting import generator
from utils import metrics
from strategies import create_strategy

def main():
    print("开始执行ETF策略回测...")
    
    all_tickers = sorted(list(set(list(config.PORTFOLIO.keys()) + config.BENCHMARKS)))
    if config.STRATEGY_CONFIG['type'] == 'sma_crossover':
        all_tickers = sorted(list(set(all_tickers + [config.STRATEGY_CONFIG['ticker_for_signal']])))
    
    try:
        # 不再需要接收 dividends_data
        prices_df = loader.get_data(
            all_tickers, config.START_DATE, config.END_DATE
        )
    except Exception as e:
        print(f"数据加载失败: {e}")
        return

    print(f"正在使用策略 '{config.STRATEGY_CONFIG['type']}' 生成交易信号...")
    strategy = create_strategy(config.STRATEGY_CONFIG)
    signals = strategy.generate_signals(prices_df)

    # 不再需要传递 dividends_data
    results_df = engine.run_backtest(config, prices_df, signals)
    
    if results_df.empty:
        print("回测没有产生任何结果，请检查日期范围或输入。")
        return

    metrics_summary = {}
    total_years = (results_df.index.max() - results_df.index.min()).days / 365.25

    portfolio_final_value = results_df['Portfolio_Value'].iloc[-1]
    total_invested = results_df['Total_Invested'].iloc[-1] if not results_df['Total_Invested'].empty else 0
    metrics_summary['Portfolio'] = {
        '最终市值': portfolio_final_value,
        '总投入本金': total_invested,
        '总收益率': (portfolio_final_value - total_invested) / total_invested if total_invested > 0 else 0,
        '年化收益率(CAGR)': metrics.calculate_cagr(portfolio_final_value, total_invested, total_years),
        '最大回撤': metrics.calculate_max_drawdown(results_df['Portfolio_Value'])
    }

    for bm in config.BENCHMARKS:
        col_name = f'{bm}_Value'
        bm_final_value = results_df[col_name].iloc[-1]
        metrics_summary[bm] = {
            '最终市值': bm_final_value,
            '总投入本金': total_invested,
            '总收益率': (bm_final_value - total_invested) / total_invested if total_invested > 0 else 0,
            '年化收益率(CAGR)': metrics.calculate_cagr(bm_final_value, total_invested, total_years),
            '最大回撤': metrics.calculate_max_drawdown(results_df[col_name])
        }

    generator.generate_report(results_df, prices_df, metrics_summary, config)
    
    print("\n回测流程全部完成。")


if __name__ == "__main__":
    main()