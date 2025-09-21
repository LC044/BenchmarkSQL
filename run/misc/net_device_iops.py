import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def plot(device, width, height):
    # 读取运行信息数据
    run_info = pd.read_csv("data/runInfo.csv")
    
    # 确定分组间隔（秒）
    xmax = run_info['runMins'].iloc[0]
    intervals = [1, 2, 5, 10, 20, 60, 120, 300, 600]
    interval = None
    for i in intervals:
        if (xmax * 60) / i <= 1000:
            interval = i
            break
    idiv = interval * 1000.0  # 转换为毫秒
    
    # 读取网络设备的IO数据并聚合
    raw_data = pd.read_csv(f"data/{device}.csv")
    
    # 聚合接收数据包数据
    raw_data['elapsed_group'] = (raw_data['elapsed'] // idiv) * idiv
    agg_recv = raw_data.groupby('elapsed_group')['rxpktsps'].mean().reset_index()
    agg_recv.columns = ['elapsed', 'rxpktsps']
    
    # 聚合发送数据包数据
    agg_send = raw_data.groupby('elapsed_group')['txpktsps'].mean().reset_index()
    agg_send.columns = ['elapsed', 'txpktsps']
    
    # 确定Y轴最大值
    ymax_rx = agg_recv['rxpktsps'].max() if not agg_recv.empty else 0
    ymax_tx = agg_send['txpktsps'].max() if not agg_send.empty else 0
    ymax = 1
    sqrt2 = np.sqrt(2.0)
    
    while ymax < ymax_rx or ymax < ymax_tx:
        ymax *= sqrt2
    
    if ymax < (ymax_rx * 1.2) or ymax < (ymax_tx * 1.2):
        ymax *= 1.2
    
    # 创建图表
    fig, ax1 = plt.subplots(figsize=(width/100, height/100), dpi=100)
    canvas = FigureCanvas(fig)
    
    # 设置边距
    plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)
    
    # 绘制接收数据包
    ax1.plot(agg_recv['elapsed'] / 60000.0, agg_recv['rxpktsps'], 
             color="blue", linewidth=2, label=f'RX Packets/s on {device}')
    ax1.set_xlabel("Elapsed Minutes")
    ax1.set_ylabel("Packets per Second")
    ax1.set_xlim(0, xmax)
    ax1.set_ylim(0, ymax)
    ax1.grid(True)
    
    # 绘制发送数据包
    ax1.plot(agg_send['elapsed'] / 60000.0, agg_send['txpktsps'], 
             color="red", linewidth=2, label=f'TX Packets/s on {device}')
    
    # 添加图例、标题和边框
    ax1.legend(loc="upper left")
    run_number = run_info['run'].iloc[0]
    driver_version = run_info['driverVersion'].iloc[0]
    plt.title(f"Run #{run_number} of BenchmarkSQL v{driver_version}\nNetwork Device {device} Packets per Second")
    plt.box(on=True)
    
    # 保存图表
    plt.savefig(f"{device}_iops.png", bbox_inches='tight')
    plt.close()
