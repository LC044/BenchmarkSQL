import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

def plot(device,width,height):
    # ----
    # Read the runInfo.csv file.
    # ----
    run_info = pd.read_csv("data/runInfo.csv")
    xmax = run_info.loc[0, "runMins"]

    # ----
    # Determine grouping interval (seconds) to keep data manageable
    # ----
    for interval in [1, 2, 5, 10, 20, 60, 120, 300, 600]:
        if (xmax * 60) / interval <= 1000:
            break
    idiv = interval * 1000.0  # convert to milliseconds

    # ----
    # Read block device IO data and aggregate
    # ----
    raw_data = pd.read_csv(f"data/{device}.csv")

    # Grouping
    raw_data["elapsed_group"] = (raw_data["elapsed"] // idiv) * idiv

    agg_reads = raw_data.groupby("elapsed_group")["rdkbps"].mean().reset_index()
    agg_writes = raw_data.groupby("elapsed_group")["wrkbps"].mean().reset_index()

    # ----
    # Determine ymax for plotting, step by sqrt(2) up until data fits
    # ----
    ymax_rd = agg_reads["rdkbps"].max()
    ymax_wr = agg_writes["wrkbps"].max()
    ymax = 1.0
    sqrt2 = math.sqrt(2.0)

    while ymax < max(ymax_rd, ymax_wr):
        ymax *= sqrt2

    if ymax < ymax_rd * 1.2 or ymax < ymax_wr * 1.2:
        ymax *= 1.2

    while ymax < ymax_rd or ymax < ymax_wr:
        ymax *= sqrt2
    if ymax < ymax_rd * 1.2 or ymax < ymax_wr * 1.2:
        ymax *= 1.2

    # 绘图
    plt.figure(figsize=(width / 100, height / 100))
    plt.plot(
        agg_reads["elapsed_group"] / 60000.0,
        agg_reads["rdkbps"],
        color="blue",
        linewidth=2,
        label=f"Read Kb/s on {device}"
    )
    plt.plot(
        agg_writes["elapsed_group"] / 60000.0,
        agg_writes["wrkbps"],
        color="red",
        linewidth=2,
        label=f"Write Kb/s on {device}"
    )

    plt.xlabel("Elapsed Minutes")
    plt.ylabel("Kilobytes per Second")
    plt.title(f"Run #{run_info.loc[0, 'run']} of BenchmarkSQL v{run_info.loc[0, 'driverVersion']}\nBlock Device {device} Kb/s")
    plt.xlim(0, xmax)
    plt.ylim(0, ymax)
    plt.grid(True)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(f"{device}_kbps.png")
    plt.close()
