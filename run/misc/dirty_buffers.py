import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot(width,height):

    # ----
    # Read runInfo.csv
    # ----
    run_info_path = os.path.join('.', "data", "runInfo.csv")
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
    # Read system info (vmstat) data
    # ----
    sysinfo_path = os.path.join('.', "data", "sys_info.csv")
    data = pd.read_csv(sysinfo_path)
    data["group"] = (data["elapsed"] // idiv) * idiv
    agg_dirty = data.groupby("group")["vm_nr_dirty"].mean().reset_index()

    # ----
    # Determine ymax
    # ----
    ymax_dirty = agg_dirty["vm_nr_dirty"].max()
    sqrt2 = np.sqrt(2.0)
    ymax = 1
    while ymax < ymax_dirty:
        ymax *= sqrt2
    if ymax < ymax_dirty * 1.2:
        ymax *= 1.2

    # ----
    # Plot
    # ----
    plt.figure(figsize=(width/100, height/100))
    plt.plot(agg_dirty["group"] / 60000.0, agg_dirty["vm_nr_dirty"], color="red", linewidth=2)

    plt.xlabel("Elapsed Minutes")
    plt.ylabel("Number dirty kernel buffers")
    plt.title(f"Run #{run_info['run'][0]} of BenchmarkSQL v{run_info['driverVersion'][0]}\nDirty Kernel Buffers")
    plt.xlim(0, xmax)
    plt.ylim(0, ymax)
    plt.legend(["vmstat nr_dirty"], loc="upper left")
    plt.grid(True)
    plt.tight_layout()

    # ----
    # Save image
    # ----
    output_path = "dirty_buffers.png"
    plt.savefig(output_path)
