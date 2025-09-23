import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from pathlib import Path

def plot(width, height):
    # 读取runInfo.csv文件
    run_info = pd.read_csv("data/runInfo.csv")
    
    # 确定分组间隔（秒）
    xmax = run_info['runMins'].iloc[0]
    intervals = [1, 2, 5, 10, 20, 60, 120, 300, 600]
    interval = 600  # 默认值
    for i in intervals:
        if (xmax * 60) / i <= 1000:
            interval = i
            break
    idiv = interval * 1000.0  # 转换为毫秒
    
    # 读取result.csv并按交易类型筛选数据
    raw_data = pd.read_csv("data/result.csv")
    no_bg_data = raw_data[raw_data['ttype'] != 'DELIVERY_BG']
    
    # 按交易类型筛选数据
    transaction_types = {
        'NEW_ORDER': raw_data[raw_data['ttype'] == 'NEW_ORDER'],
        'PAYMENT': raw_data[raw_data['ttype'] == 'PAYMENT'],
        'ORDER_STATUS': raw_data[raw_data['ttype'] == 'ORDER_STATUS'],
        'STOCK_LEVEL': raw_data[raw_data['ttype'] == 'STOCK_LEVEL'],
        'DELIVERY': raw_data[raw_data['ttype'] == 'DELIVERY'],
        'DELIVERY_BG': raw_data[raw_data['ttype'] == 'DELIVERY_BG']
    }
    
    # 按时间间隔聚合延迟数据
    agg_data = {}
    for name, data in transaction_types.items():
        if name == 'DELIVERY_BG':  # 跳过背景交付
            continue
        # 计算时间间隔分组
        data['elapsed_group'] = (data['elapsed'] / idiv).apply(math.trunc) * idiv
        # 按分组计算平均延迟
        agg = data.groupby('elapsed_group')['latency'].mean().reset_index()
        agg.columns = ['elapsed', 'latency']
        agg_data[name] = agg
    
    # 确定Y轴最大值
    ymax_total = no_bg_data['latency'].quantile(0.98)
    ymax = 1.0
    sqrt2 = math.sqrt(2.0)
    while ymax < ymax_total:
        ymax *= sqrt2
    if ymax < (ymax_total * 1.2):
        ymax *= 1.2
    
    # 设置绘图风格和大小
    plt.figure(figsize=(12, 8))
    plt.subplots_adjust()
    
    # 定义颜色映射
    colors = {
        'DELIVERY': 'blue',
        'STOCK_LEVEL': 'gray',
        'ORDER_STATUS': 'green',
        'PAYMENT': 'magenta',
        'NEW_ORDER': 'red'
    }
    
    # 绘制各个交易类型的延迟曲线
    for name in ['DELIVERY', 'STOCK_LEVEL', 'ORDER_STATUS', 'PAYMENT', 'NEW_ORDER']:
        data = agg_data[name]
        # 转换为分钟
        x = data['elapsed'] / 60000.0
        y = data['latency']
        
        if name == 'DELIVERY':  # 第一个绘图设置坐标轴
            plt.plot(x, y, color=colors[name], linewidth=2, label=name)
            plt.xlabel('Elapsed Minutes')
            plt.ylabel('Latency in Milliseconds')
            plt.xlim(0, xmax)
            plt.ylim(0, ymax)
        else:  # 后续绘图共享坐标轴
            plt.plot(x, y, color=colors[name], linewidth=2, label=name)
    
    # 添加图例、标题和其他装饰
    plt.legend(loc='upper left')
    plt.title(f"Run #{run_info['run'].iloc[0]} of BenchmarkSQL v{run_info['driverVersion'].iloc[0]}\nTransaction Latency")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.box(on=True)
    
    # 保存图像
    plt.savefig('latency.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 生成交易摘要并写入CSV
    tx_total = len(no_bg_data)
    run_mins = run_info['runMins'].iloc[0]
    run_warehouses = run_info['runWarehouses'].iloc[0]
    
    # 准备摘要数据
    summary_data = {
        'tx_name': ['NEW_ORDER', 'PAYMENT', 'ORDER_STATUS', 'STOCK_LEVEL', 'DELIVERY', 'DELIVERY_BG', 'tpmC', 'tpmTotal'],
        'tx_count': [
            len(transaction_types['NEW_ORDER']),
            len(transaction_types['PAYMENT']),
            len(transaction_types['ORDER_STATUS']),
            len(transaction_types['STOCK_LEVEL']),
            len(transaction_types['DELIVERY']),
            len(transaction_types['DELIVERY_BG']),
            f"{len(transaction_types['NEW_ORDER']) / run_mins:.2f}",
            f"{len(no_bg_data) / run_mins:.2f}"
        ],
        'tx_percent': [
            f"{len(transaction_types['NEW_ORDER']) / tx_total * 100:.3f}%",
            f"{len(transaction_types['PAYMENT']) / tx_total * 100:.3f}%",
            f"{len(transaction_types['ORDER_STATUS']) / tx_total * 100:.3f}%",
            f"{len(transaction_types['STOCK_LEVEL']) / tx_total * 100:.3f}%",
            f"{len(transaction_types['DELIVERY']) / tx_total * 100:.3f}%",
            None,
            f"{(len(transaction_types['NEW_ORDER']) / run_mins) / run_warehouses / 0.1286:.3f}%",
            None
        ],
        'tx_90th': [
            f"{transaction_types['NEW_ORDER']['latency'].quantile(0.90) / 1000:.3f}s",
            f"{transaction_types['PAYMENT']['latency'].quantile(0.90) / 1000:.3f}s",
            f"{transaction_types['ORDER_STATUS']['latency'].quantile(0.90) / 1000:.3f}s",
            f"{transaction_types['STOCK_LEVEL']['latency'].quantile(0.90) / 1000:.3f}s",
            f"{transaction_types['DELIVERY']['latency'].quantile(0.90) / 1000:.3f}s",
            f"{transaction_types['DELIVERY_BG']['latency'].quantile(0.90) / 1000:.3f}s",
            None, None
        ],
        'tx_max': [
            f"{transaction_types['NEW_ORDER']['latency'].max() / 1000:.3f}s",
            f"{transaction_types['PAYMENT']['latency'].max() / 1000:.3f}s",
            f"{transaction_types['ORDER_STATUS']['latency'].max() / 1000:.3f}s",
            f"{transaction_types['STOCK_LEVEL']['latency'].max() / 1000:.3f}s",
            f"{transaction_types['DELIVERY']['latency'].max() / 1000:.3f}s",
            f"{transaction_types['DELIVERY_BG']['latency'].max() / 1000:.3f}s",
            None, None
        ],
        'tx_limit': ["5.0", "5.0", "5.0", "20.0", "5.0", "80.0", None, None],
        'tx_rbk': [
            f"{transaction_types['NEW_ORDER']['rbk'].sum() / len(transaction_types['NEW_ORDER']) * 100:.3f}%",
            None, None, None, None, None, None, None
        ],
        'tx_error': [
            transaction_types['NEW_ORDER']['error'].sum(),
            transaction_types['PAYMENT']['error'].sum(),
            transaction_types['ORDER_STATUS']['error'].sum(),
            transaction_types['STOCK_LEVEL']['error'].sum(),
            transaction_types['DELIVERY']['error'].sum(),
            transaction_types['DELIVERY_BG']['error'].sum(),
            None, None
        ],
        'tx_dskipped': [
            None, None, None, None, None,
            transaction_types['DELIVERY_BG']['dskipped'].sum(),
            None, None
        ]
    }
    
    # 创建DataFrame并替换NaN为N/A
    tx_info = pd.DataFrame(summary_data)
    # 1. 整体转为字符串类型
    tx_info = tx_info.astype(str)

    # 2. 填充缺失值（此时"N/A"与字符串类型兼容）
    tx_info = tx_info.replace('nan', 'N/A')
    # tx_info.fillna("N/A", inplace=True)
    
    # 保存摘要数据
    tx_info.to_csv("data/tx_summary.csv", index=False)

# 调用函数执行绘图和数据处理
if __name__ == "__main__":
    plot(1,1)
