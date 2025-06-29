import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

    # 生成 Plotly 图表的 HTML 代码片段
    charts_html = _generate_interactive_charts(results_df, prices_df, config)
    print("交互式图表已生成。")

    html_path = os.path.join(output_dir, 'summary_report.html')
    _generate_html_report(metrics_summary, charts_html, config, html_path)
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


def _generate_interactive_charts(results_df, prices_df, config):
    """
    使用 Plotly 生成所有交互式图表，并返回其HTML代码。
    """
    charts_html = {}
    
    # --- 图表1: 资产增长曲线 ---
    fig_growth = go.Figure()
    for col in results_df.columns:
        if '_Value' in col or 'Invested' in col:
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '').replace('Total_Invested', 'Total Invested')
            fig_growth.add_trace(go.Scatter(x=results_df.index, y=results_df[col], mode='lines', name=label))
            
    fig_growth.update_layout(
        title_text='<b>Asset Growth Curve</b>',
        xaxis_title='Date',
        yaxis_title='Market Value ($)',
        legend_title_text='Legend',
        hovermode='x unified' # 统一的X轴悬停效果
    )
    charts_html['growth'] = fig_growth.to_html(full_html=False, include_plotlyjs='cdn')

    # --- 图表2: 回撤曲线 ---
    fig_drawdown = go.Figure()
    for col in results_df.columns:
        if '_Value' in col:
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '')
            cumulative_max = results_df[col].cummax()
            drawdown = (results_df[col] - cumulative_max) / cumulative_max
            fig_drawdown.add_trace(go.Scatter(x=drawdown.index, y=drawdown, mode='lines', name=label))
            
    fig_drawdown.update_layout(
        title_text='<b>Drawdown Curve</b>',
        xaxis_title='Date',
        yaxis_title='Drawdown',
        yaxis_tickformat='.0%', # Y轴格式化为百分比
        hovermode='x unified'
    )
    charts_html['drawdown'] = fig_drawdown.to_html(full_html=False, include_plotlyjs='cdn')

    # --- 图表3: 各投资标的价格走势 (归一化) ---
    fig_price = go.Figure()
    all_tickers = sorted(list(set(list(config.PORTFOLIO.keys()) + config.BENCHMARKS)))
    if config.STRATEGY_CONFIG['type'] == 'sma_crossover':
        all_tickers = sorted(list(set(all_tickers + [config.STRATEGY_CONFIG['ticker_for_signal']])))

    valid_tickers = [t for t in all_tickers if t in prices_df.columns]
    if valid_tickers:
        normalized_prices = (prices_df[valid_tickers] / prices_df[valid_tickers].iloc[0]) * 100
        for ticker in valid_tickers:
            fig_price.add_trace(go.Scatter(x=normalized_prices.index, y=normalized_prices[ticker], mode='lines', name=ticker))
            
        fig_price.update_layout(
            title_text='<b>Normalized Price Performance of All Assets</b>',
            xaxis_title='Date',
            yaxis_title='Normalized Price (Start = 100)',
            hovermode='x unified'
        )
        charts_html['price_performance'] = fig_price.to_html(full_html=False, include_plotlyjs='cdn')

    return charts_html


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


def _generate_html_report(metrics_summary, charts_html, config, output_path):
    """
    将图表的HTML代码嵌入到Jinja2模板中。
    """
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
        # 传递图表的HTML代码
        "growth_chart_html": charts_html.get('growth'),
        "drawdown_chart_html": charts_html.get('drawdown'),
        "price_performance_chart_html": charts_html.get('price_performance'),
        "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    html_out = template.render(template_vars)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)