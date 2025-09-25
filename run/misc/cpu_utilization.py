import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
# 设置全局字体大小
plt.rcParams['font.size'] = 14  # 影响标题、标签、图例等默认字体大小
plt.rcParams['axes.titlesize'] = 16  # 标题
plt.rcParams['axes.labelsize'] = 14  # 坐标轴标签
plt.rcParams['legend.fontsize'] = 12  # 图例
plt.rcParams['xtick.labelsize'] = 12  # x轴刻度
plt.rcParams['ytick.labelsize'] = 12  # y轴刻度
def plot(width: int = 1400, height: int = 400):
    """
    Plot CPU utilization over time using data from BenchmarkSQL.

    Args:
        width (int): Width of the image in pixels.
        height (int): Height of the image in pixels.
    """

    # Read run info
    run_info = pd.read_csv("data/runInfo.csv")
    xmax = run_info.loc[0, "runMins"]

    # Determine grouping interval (in ms)
    for interval in [1, 2, 5, 10, 20, 60, 120, 300, 600]:
        if (xmax * 60) / interval <= 1000:
            break
    idiv = interval * 1000.0

    # Read and aggregate system info
    raw_data = pd.read_csv("data/sys_info.csv")
    raw_data["elapsed_group"] = (raw_data["elapsed"] // idiv) * idiv

    agg_user = raw_data.groupby("elapsed_group")["cpu_user"].mean().reset_index()
    agg_system = raw_data.groupby("elapsed_group")["cpu_system"].mean().reset_index()
    agg_wait = raw_data.groupby("elapsed_group")["cpu_iowait"].mean().reset_index()

    # Convert to percentage and minutes
    minutes = agg_user["elapsed_group"] / 60000.0
    user_pct = agg_user["cpu_user"] * 100.0
    system_pct = agg_system["cpu_system"] * 100.0
    wait_pct = agg_wait["cpu_iowait"] * 100.0

    user_plus_system = user_pct + system_pct
    total_cpu = user_plus_system + wait_pct

    # Plot
    plt.figure(figsize=(width / 100, height / 100))
    plt.plot(minutes, total_cpu, label="% IOWait", color="red", linewidth=2)
    plt.plot(minutes, user_plus_system, label="% System", color="cyan", linewidth=2)
    plt.plot(minutes, user_pct, label="% User", color="blue", linewidth=2)

    plt.xlabel("Elapsed Minutes")
    plt.ylabel("CPU Utilization in Percent")
    plt.legend(loc="upper left")
    plt.title(f"Run #{run_info.loc[0, 'run']} of BenchmarkSQL v{run_info.loc[0, 'driverVersion']}\nCPU Utilization")
    plt.xlim(0, xmax)
    plt.ylim(0, 100)
    
    plt.grid(True)
    plt.tight_layout() # 使用紧凑布局
    plt.savefig("cpu_utilization.png", dpi=300)
    plt.close()
