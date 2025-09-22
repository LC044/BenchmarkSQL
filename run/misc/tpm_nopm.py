import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os

def plot(height,width):
    data_file = "data/runInfo.csv"
    # ----
    # Read runInfo.csv
    # ----
    run_info = pd.read_csv(data_file)
    run_mins = run_info['runMins'][0]
    xmax = run_mins

    # ----
    # Determine grouping interval (in seconds)
    # ----
    for interval in [1, 2, 5, 10, 20, 60, 120, 300, 600]:
        if (xmax * 60) / interval <= 1000:
            break
    idiv = interval * 1000.0  # milliseconds

    # ----
    # Read result.csv and filter
    # ----
    data = pd.read_csv("data/result.csv")
    total = data[data['ttype'] != 'DELIVERY_BG'].copy()
    new_order = data[data['ttype'] == 'NEW_ORDER'].copy()

    # ----
    # Aggregate counts grouped by interval
    # ----
    total['group'] = (total['elapsed'] // idiv) * idiv
    new_order['group'] = (new_order['elapsed'] // idiv) * idiv

    count_total = total.groupby('group').size().reset_index(name='count')
    count_new_order = new_order.groupby('group').size().reset_index(name='count')

    # ----
    # Compute ymax
    # ----
    ymax_count = count_total['count'].max() * 60.0 / interval
    ymax = 1
    sqrt2 = math.sqrt(2.0)
    while ymax < ymax_count:
        ymax *= sqrt2
    if ymax < (ymax_count * 1.2):
        ymax *= 1.2

    # ----
    # Plot
    # ----
    plt.figure(figsize=(18, 6))
    plt.plot(
        count_total['group'] / 60000.0,  # convert ms to minutes
        count_total['count'] * 60.0 / interval,
        linewidth=2,
        label='tpmTOTAL',
        color='blue'
    )
    plt.plot(
        count_new_order['group'] / 60000.0,
        count_new_order['count'] * 60.0 / interval,
        linewidth=2,
        label='tpmC (NewOrder only)',
        color='red'
    )

    # ----
    # Decorations
    # ----
    plt.xlabel("Elapsed Minutes")
    plt.ylabel("Transactions per Minute")
    plt.title(f"Run #{run_info['run'][0]} of BenchmarkSQL v{run_info['driverVersion'][0]}\nTransactions per Minute")
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.xlim(0, xmax)
    plt.ylim(0, ymax)
    plt.tight_layout()

    # ----
    # Save figure
    # ----
    plt.savefig("tpm_nopm.png")
    plt.close()
