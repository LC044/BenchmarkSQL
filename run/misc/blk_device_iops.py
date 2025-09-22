import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os


def plot(device,width,height):
    # ----
    # Read runInfo.csv
    # ----
    run_info_path = "data/runInfo.csv"
    run_info = pd.read_csv(run_info_path)
    xmax = float(run_info["runMins"][0])

    # ----
    # Determine grouping interval
    # ----
    for interval in [1, 2, 5, 10, 20, 60, 120, 300, 600]:
        if (xmax * 60) / interval <= 1000:
            break
    idiv = interval * 1000.0

    # ----
    # Read block device I/O data
    # ----
    data_path = f"data/{device}.csv"
    data = pd.read_csv(data_path)

    data["group"] = (data["elapsed"] // idiv) * idiv
    agg_reads = data.groupby("group")["rdiops"].mean().reset_index()
    agg_writes = data.groupby("group")["wriops"].mean().reset_index()

    # ----
    # Compute ymax for plotting
    # ----
    ymax_rd = agg_reads["rdiops"].max()
    ymax_wr = agg_writes["wriops"].max()
    ymax = 1
    sqrt2 = np.sqrt(2.0)
    while ymax < max(ymax_rd, ymax_wr):
        ymax *= sqrt2
    if ymax < max(ymax_rd, ymax_wr) * 1.2:
        ymax *= 1.2

    # ----
    # Plot
    # ----
    plt.figure(figsize=(width/100, height/100))
    plt.plot(agg_reads["group"] / 60000.0, agg_reads["rdiops"], linewidth=2, label=f"Read Operations on {device}", color="blue")
    plt.plot(agg_writes["group"] / 60000.0, agg_writes["wriops"], linewidth=2, label=f"Write Operations on {device}", color="red")

    plt.xlabel("Elapsed Minutes")
    plt.ylabel("IO Operations per Second")
    plt.title(f"Run #{run_info['run'][0]} of BenchmarkSQL v{run_info['driverVersion'][0]}\nBlock Device {device} IOPS")
    plt.xlim(0, xmax)
    plt.ylim(0, ymax)
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.tight_layout()

    # ----
    # Save image
    # ----
    output_path = os.path.join('.', f"{device}_iops.png")
    plt.savefig(output_path)
