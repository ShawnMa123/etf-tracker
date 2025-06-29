import pandas as pd
import config
from data import loader
from backtesting import engine
from reporting import generator
from utils import metrics

def main():
    """
    项目主入口函数
    """
    print("开始执行ETF定投回测...")
    
    # 1. 加载配置并准备代码列表
    all_tickers = list(config.PORTFOLIO.keys()) + config.BENCHMARKS
    # 去重
    all_tickers = sorted(list(set(all_tickers)))
    
    # 2. 获取数据
    try:
        prices_df, dividends_data = loader.get_data(
            all_tickers, config.START_DATE, config.END_DATE
        )
    except Exception as e:
        print(f"数据加载失败: {e}")
        return

    # 3. 运行回测引擎
    results_df = engine.run_backtest(config, prices_df, dividends_data)
    
    if results_df.empty:
        print("回测没有产生任何结果，请检查日期范围或输入。")
        return

    # 4. 计算最终性能指标
    metrics_summary = {}
    
    # 计算投资总年数
    total_years = (results_df.index.max() - results_df.index.min()).days / 365.25

    # 计算用户投资组合指标
    portfolio_final_value = results_df['Portfolio_Value'].iloc[-1]
    total_invested = results_df['Total_Invested'].iloc[-1]
    metrics_summary['Portfolio'] = {
        '最终市值': portfolio_final_value,
        '总投入本金': total_invested,
        '总收益率': (portfolio_final_value - total_invested) / total_invested if total_invested > 0 else 0,
        '年化收益率(CAGR)': metrics.calculate_cagr(portfolio_final_value, total_invested, total_years),
        '最大回撤': metrics.calculate_max_drawdown(results_df['Portfolio_Value'])
    }

    # 计算基准指标
    for bm in config.BENCHMARKS:
        col_name = f'{bm}_Value'
        bm_final_value = results_df[col_name].iloc[-1]
        metrics_summary[bm] = {
            '最终市值': bm_final_value,
            '总投入本金': total_invested, # 基准使用相同的投入金额
            '总收益率': (bm_final_value - total_invested) / total_invested if total_invested > 0 else 0,
            '年化收益率(CAGR)': metrics.calculate_cagr(bm_final_value, total_invested, total_years),
            '最大回撤': metrics.calculate_max_drawdown(results_df[col_name])
        }

    # 5. 生成报告
    generator.generate_report(results_df, metrics_summary, config)
    
    print("\n回测流程全部完成。")


if __name__ == "__main__":
    main()