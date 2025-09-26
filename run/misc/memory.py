import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
# 设置全局字体大小
plt.rcParams['font.size'] = 14  # 影响标题、标签、图例等默认字体大小
plt.rcParams['axes.titlesize'] = 16  # 标题
plt.rcParams['axes.labelsize'] = 14  # 坐标轴标签
plt.rcParams['legend.fontsize'] = 12  # 图例
plt.rcParams['xtick.labelsize'] = 12  # x轴刻度
plt.rcParams['ytick.labelsize'] = 12  # y轴刻度
def main():
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("用法: python memory_usage_plot.py <日志文件路径>")
        sys.exit(1)
    
    # 获取命令行输入的日志文件路径
    log_file = sys.argv[1]
    
    # 验证文件是否存在
    if not os.path.exists(log_file):
        print(f"错误: 文件 '{log_file}' 不存在")
        sys.exit(1)
    
    # 用来存储数据
    timestamps = []
    used_mem = []
    total_mem = []
    
    # 匹配日志中时间和 Memory Usage
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Memory Usage: (\d+)MB / (\d+)MB")
    
    with open(log_file, "r") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                timestamps.append(match.group(1))
                used_mem.append(int(match.group(2)))
                total_mem.append(int(match.group(3)))
    
    if not timestamps:
        print("警告: 未在日志文件中找到任何内存使用记录")
        sys.exit(0)
    
    # 构建 DataFrame
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps),
        "used_mb": used_mem,
        "total_mb": total_mem
    })
    if len(used_mem) > 0:
        used_mem_mean = df["used_mb"].sum() / len(used_mem)
        used_mem_max = df["used_mb"].max()
        used_mem_min = df["used_mb"].min()
    else:
        used_mem_mean = 0
        used_mem_max = 0
        used_mem_min = 0
    if len(total_mem) > 0:
        total_mem_mean = df["total_mb"].sum() / len(total_mem)
        total_mem_max = df["total_mb"].max()
        total_mem_min = df["total_mb"].min()
    else:
        total_mem_mean = 0
        total_mem_max = 0
        total_mem_min = 0
    ymax = total_mem_max * 1.2
    xmax = len(total_mem)

    # 计算相对时间（分钟），从0开始
    start_time = df["timestamp"].iloc[0]
    df["minutes_since_start"] = (df["timestamp"] - start_time).dt.total_seconds() / 60
    # 假设t为时间数组（如0到60分钟，步长0.1分钟），y为对应内存使用数据
    t = df["minutes_since_start"]  
    y = df["used_mb"]  # 替换为从图中提取的内存使用数据（需与t长度一致）

    # 执行傅里叶变换
    fft_vals = np.fft.fft(y)            # 傅里叶变换结果（复数）
    freqs = np.fft.fftfreq(len(t), t[1]-t[0])  # 频率数组（单位：1/分钟）

    # 计算振幅（取复数的模），排除直流分量（0频率）
    fft_amps = np.abs(fft_vals)
    dominant_freq_idx = np.argmax(fft_amps[1:]) + 1  # 找到最大振幅的频率索引（跳过0频率）
    dominant_freq = freqs[dominant_freq_idx]         # 主导频率

    # 计算平均周期
    average_period = 1 / dominant_freq
    print(f"平均周期：{average_period:.2f} 分钟")
    with open(log_file, "a") as f:
        f.write(f"Max memory usage: {used_mem_max:.0f}MB / {total_mem_max:.0f}MB\n")
        f.write(f"Min memory usage: {used_mem_min:.0f}MB / {total_mem_min:.0f}MB\n")
        f.write(f"Max-min memory usage: {used_mem_max-used_mem_min:.0f}MB / {total_mem_max-total_mem_min:.0f}MB\n")
        f.write(f"Average memory usage: {used_mem_mean:.0f}MB / {total_mem_mean:.0f}MB\n")
        # 写入平均周期
        f.write(f"Average period: {average_period:.2f} minutes\n")

    
    # 绘制曲线
    plt.figure(figsize=(18, 6), dpi=100)
    # 设置边距
    plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)
    plt.plot(df["minutes_since_start"], df["used_mb"], label="Used Memory (MB)", linewidth=2, color="blue")
    plt.plot(df["minutes_since_start"], df["total_mb"], label="Total Memory (MB)", linewidth=2, color="orange", linestyle="--")
    # plt.xlim(0, xmax)
    plt.ylim(0, ymax)
    plt.xlabel("Minutes Since Start")
    plt.ylabel("Memory (MB)")
    plt.legend(loc='upper left')
    plt.title("BenchmarkSQL Memory Usage Over Time")

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.box(on=True)

    # 获取日志文件所在目录
    log_dir = os.path.dirname(log_file)
    # 构建图片保存路径（与日志文件同目录）
    image_path = os.path.join(log_dir, "memory_usage_curve.png")
    
    # 保存图片
    plt.tight_layout()
    plt.savefig(image_path, dpi=300)
    plt.close()
    print(f"曲线已保存为 {image_path}")

if __name__ == "__main__":
    main()
