import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

def plot(device, width, height):
    # 读取运行信息数据
    run_info = pd.read_csv("data/runInfo.csv")
    xmax = run_info['runMins'].iloc[0]  # 获取运行分钟数
    
    # 确定分组间隔（秒）
    intervals = [1, 2, 5, 10, 20, 60, 120, 300, 600]
    interval = 600  # 默认最大间隔
    for int_val in intervals:
        if (xmax * 60) / int_val <= 1000:
            interval = int_val
            break
    idiv = interval * 1000.0  # 转换为毫秒
    
    # 读取网络设备数据
    raw_data = pd.read_csv(f"data/{device}.csv")
    
    # 聚合接收数据
    raw_data['recv_group'] = (raw_data['elapsed'] / idiv).apply(np.trunc) * idiv
    agg_recv = raw_data.groupby('recv_group')['rxkbps'].mean().reset_index()
    agg_recv.columns = ['elapsed', 'rxkbps']
    
    # 聚合发送数据
    raw_data['send_group'] = (raw_data['elapsed'] / idiv).apply(np.trunc) * idiv
    agg_send = raw_data.groupby('send_group')['txkbps'].mean().reset_index()
    agg_send.columns = ['elapsed', 'txkbps']
    
    # 确定Y轴最大值
    ymax_rx = agg_recv['rxkbps'].max() if not agg_recv.empty else 0
    ymax_tx = agg_send['txkbps'].max() if not agg_send.empty else 0
    ymax = 1.0
    sqrt2 = np.sqrt(2.0)
    
    while ymax < ymax_rx or ymax < ymax_tx:
        ymax *= sqrt2
    
    # 增加一点余量
    if ymax < (ymax_rx * 1.2) or ymax < (ymax_tx * 1.2):
        ymax *= 1.2
    
    # 创建图形
    plt.style.use('default')
    fig, ax1 = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    # 绘制接收速率
    ax1.plot(agg_recv['elapsed'] / 60000.0, agg_recv['rxkbps'], 
             color='blue', linewidth=2, label=f'RX Kb/s on {device}')
    ax1.set_xlabel('Elapsed Minutes')
    ax1.set_ylabel('Kilobytes per Second')
    ax1.set_xlim(0, xmax)
    ax1.set_ylim(0, ymax)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 绘制发送速率
    ax1.plot(agg_send['elapsed'] / 60000.0, agg_send['txkbps'], 
             color='red', linewidth=2, label=f'TX Kb/s on {device}')
    
    # 添加标题和图例
    run_number = run_info['run'].iloc[0]
    driver_version = run_info['driverVersion'].iloc[0]
    plt.title(f'Run #{run_number} of BenchmarkSQL v{driver_version}\nNetwork Device {device} Kb per Second')
    ax1.legend(loc='upper left')
    
    # 添加边框
    for spine in ax1.spines.values():
        spine.set_edgecolor('black')
    
    # 保存图像
    plt.tight_layout()
    plt.savefig(f"{device}_kbps.png", bbox_inches='tight')
    plt.close()
