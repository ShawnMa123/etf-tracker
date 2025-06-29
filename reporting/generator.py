import os
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from tabulate import tabulate

def generate_report(results_df, metrics_summary, config):
    """
    生成所有输出文件的主函数。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    portfolio_name = "_".join(config.PORTFOLIO.keys())
    output_dir = os.path.join("results", f"report_{portfolio_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n报告生成中，文件将保存在: {output_dir}")

    # 终端输出保持中文
    _generate_console_output(metrics_summary)

    csv_path = os.path.join(output_dir, 'daily_results.csv')
    results_df.to_csv(csv_path)
    print(f"每日数据已保存到: {csv_path}")

    # 生成全英文图表
    chart_paths = _generate_charts(results_df, output_dir)
    print("图表已生成。")

    # HTML报告保持中文
    html_path = os.path.join(output_dir, 'summary_report.html')
    _generate_html_report(metrics_summary, chart_paths, config, html_path)
    print(f"HTML报告已生成: {html_path}")

def _generate_console_output(metrics_summary):
    # 此函数保持不变，继续使用中文
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

def _generate_charts(results_df, output_dir):
    # --- FIX: 移除所有字体设置，并将所有文本改为英文 ---
    plt.style.use('seaborn-v0_8-whitegrid')
    chart_paths = {}

    # 资产增长曲线 (Asset Growth Curve)
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    for col in results_df.columns:
        if '_Value' in col or 'Invested' in col:
            # 翻译图例
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '').replace('Total_Invested', 'Total Invested')
            ax1.plot(results_df.index, results_df[col], label=label)
    
    # 翻译标题和坐标轴
    ax1.set_title('Asset Growth Curve', fontsize=16)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Market Value ($)')
    ax1.legend()
    ax1.grid(True)
    growth_chart_path = os.path.join(output_dir, 'growth_curve.png')
    plt.savefig(growth_chart_path)
    plt.close(fig1)
    chart_paths['growth'] = 'growth_curve.png'

    # 回撤曲线 (Drawdown Curve)
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    from utils.metrics import calculate_max_drawdown
    for col in results_df.columns:
        if '_Value' in col:
            # 翻译图例
            label = 'Portfolio' if col == 'Portfolio_Value' else col.replace('_Value', '')
            cumulative_max = results_df[col].cummax()
            drawdown = (results_df[col] - cumulative_max) / cumulative_max
            ax2.plot(drawdown.index, drawdown, label=label, alpha=0.7)

    # 翻译标题和坐标轴
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

    return chart_paths


def _generate_html_report(metrics_summary, chart_paths, config, output_path):
    # 此函数保持不变，继续使用中文
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
        "investment_strategy": f"每周{config.INVESTMENT_DAY}定投 ${config.INVESTMENT_AMOUNT:,.2f}",
        "metrics_table": html_table,
        "growth_chart_path": chart_paths['growth'],
        "drawdown_chart_path": chart_paths['drawdown'],
        "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    html_out = template.render(template_vars)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)