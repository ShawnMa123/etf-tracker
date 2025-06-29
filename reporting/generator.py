import os
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from tabulate import tabulate

def generate_report(results_df, prices_df, metrics_summary, config):
    """
    生成所有输出文件的主函数。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    portfolio_name = "_".join(config.PORTFOLIO.keys())
    output_dir = os.path.join("results", f"report_{portfolio_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n报告生成中，文件将保存在: {output_dir}")

    _generate_console_output(metrics_summary)

    csv_path = os.path.join(output_dir, 'daily_results.csv')
    results_df.to_csv(csv_path)
    print(f"每日数据已保存到: {csv_path}")

    # --- FIX: 将 output_dir 作为参数传递给 _generate_charts ---
    chart_paths = _generate_charts(results_df, prices_df, config, output_dir)
    print("图表已生成。")

    html_path = os.path.join(output_dir, 'summary_report.html')
    _generate_html_report(metrics_summary, chart_paths, config, html_path)
    print(f"HTML报告已生成: {html_path}")


def _generate_console_output(metrics_summary):
    # 此函数无变化
    headers = ["指标"] + list(metrics_summary.keys())
    table = []
    metric_order = ['最终市值', '总投入本金', '总收益率', '年化收益率(CAGR)', '最大回撤']
    for metric_name in metric_order:
        row = [metric_name]
        for name in headers[1:]:
            value = metrics_summary[name][metric_name]
            if isinstance(value, float) and "率" in metric_name or "回撤" in metric_name:
                row.append(f"{value:.2%}")
            elif isinstance(value, float):
                row.append(f"${value:,.2f}")
            else:
                row.append(value)
        table.append(row)
    
    print("\n" + "="*20 + " 回测结果摘要 " + "="*20)
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("="*54)


# --- FIX: 在函数签名中接收 output_dir 参数 ---
def _generate_charts(results_df, prices_df, config, output_dir):
    """
    生成所有图表并保存到指定的输出目录。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    chart_paths = {}

    # 资产增长曲线
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    for col in results_df.columns:
        if '_Value' in col or 'Invested' in col:
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '').replace('Total_Invested', 'Total Invested')
            ax1.plot(results_df.index, results_df[col], label=label)
    
    ax1.set_title('Asset Growth Curve', fontsize=16)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Market Value ($)')
    ax1.legend()
    ax1.grid(True)
    # 现在 output_dir 在这里是已定义的
    growth_chart_path = os.path.join(output_dir, 'growth_curve.png')
    plt.savefig(growth_chart_path)
    plt.close(fig1)
    chart_paths['growth'] = 'growth_curve.png'

    # 回撤曲线
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    from utils.metrics import calculate_max_drawdown
    for col in results_df.columns:
        if '_Value' in col:
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '')
            cumulative_max = results_df[col].cummax()
            drawdown = (results_df[col] - cumulative_max) / cumulative_max
            ax2.plot(drawdown.index, drawdown, label=label, alpha=0.7)

    ax2.set_title('Drawdown Curve', fontsize=16)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter('{:.0%}'.format))
    ax2.legend()
    ax2.grid(True)
    drawdown_chart_path = os.path.join(output_dir, 'drawdown_curve.png')
    plt.savefig(drawdown_chart_path)
    plt.close(fig2)
    chart_paths['drawdown'] = 'drawdown_curve.png'

    # 各投资标的价格走势
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    all_tickers = sorted(list(set(list(config.PORTFOLIO.keys()) + config.BENCHMARKS)))
    if config.STRATEGY_CONFIG['type'] == 'sma_crossover':
        all_tickers = sorted(list(set(all_tickers + [config.STRATEGY_CONFIG['ticker_for_signal']])))

    # 确保所有tickers都在prices_df中，避免KeyError
    valid_tickers = [t for t in all_tickers if t in prices_df.columns]
    if not valid_tickers:
        print("警告: 无法生成价格走势图，因为没有有效的tickers。")
        return chart_paths
        
    normalized_prices = (prices_df[valid_tickers] / prices_df[valid_tickers].iloc[0]) * 100
    
    for ticker in valid_tickers:
        ax3.plot(normalized_prices.index, normalized_prices[ticker], label=ticker)
        
    ax3.set_title('Normalized Price Performance of All Assets', fontsize=16)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Normalized Price (Start = 100)')
    ax3.legend()
    ax3.grid(True)
    price_chart_path = os.path.join(output_dir, 'price_performance.png')
    plt.savefig(price_chart_path)
    plt.close(fig3)
    chart_paths['price_performance'] = 'price_performance.png'

    return chart_paths


def _get_strategy_description(config):
    # 此函数无变化
    strategy_conf = config.STRATEGY_CONFIG
    strategy_type = strategy_conf.get('type')
    amount = config.INVESTMENT_AMOUNT

    if strategy_type == 'time_based':
        freq = strategy_conf.get('frequency')
        day = strategy_conf.get('day')
        freq_map = {'weekly': '每周', 'bi-weekly': '双周', 'monthly': '每月'}
        day_map_weekly = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五'}
        
        desc = f"{freq_map.get(freq, freq)}"
        if freq in ['weekly', 'bi-weekly']:
            desc += f"{day_map_weekly.get(day, '')}"
        else:
            desc += f"{day}号"
        desc += f"定投 ${amount:,.2f}"
        return desc
    
    elif strategy_type == 'sma_crossover':
        ticker = strategy_conf.get('ticker_for_signal')
        short = strategy_conf.get('short_window')
        long = strategy_conf.get('long_window')
        return f"基于 {ticker} 的 {short}/{long}日均线金叉策略，每次买入 ${amount:,.2f}"
        
    else:
        return f"自定义策略, 每次买入 ${amount:,.2f}"


def _generate_html_report(metrics_summary, chart_paths, config, output_path):
    # 此函数无变化
    env = Environment(loader=FileSystemLoader(os.path.join('reporting', 'templates')))
    template = env.get_template('report_template.html')

    headers = ["指标"] + list(metrics_summary.keys())
    rows = []
    metric_order = ['最终市值', '总投入本金', '总收益率', '年化收益率(CAGR)', '最大回撤']
    for metric_name in metric_order:
        row = [metric_name]
        for name in headers[1:]:
            value = metrics_summary[name][metric_name]
            if isinstance(value, float) and "率" in metric_name or "回撤" in metric_name:
                row.append(f"{value:.2%}")
            elif isinstance(value, float):
                row.append(f"${value:,.2f}")
            else:
                row.append(value)
        rows.append(row)

    html_table = tabulate(rows, headers=headers, tablefmt="html")
    
    template_vars = {
        "portfolio_name": " / ".join(config.PORTFOLIO.keys()),
        "start_date": config.START_DATE,
        "end_date": config.END_DATE,
        "investment_strategy": _get_strategy_description(config),
        "metrics_table": html_table,
        "growth_chart_path": chart_paths.get('growth'),
        "drawdown_chart_path": chart_paths.get('drawdown'),
        "price_performance_chart_path": chart_paths.get('price_performance'),
        "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    html_out = template.render(template_vars)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)