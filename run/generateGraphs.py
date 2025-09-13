import os
import sys
import glob

# 图像尺寸
WIDTH = 1800
HEIGHT = 600

# 简单图表列表
SIMPLE_GRAPHS = [
    "tpm_nopm",
    # "latency",
    "cpu_utilization",
    "dirty_buffers"
]

# 假设你已经实现的函数
from misc import (
    tpm_nopm,
    blk_device_iops,
    blk_device_kbps,
    dirty_buffers,
    cpu_utilization,
)

graph_func_map = {
    "tpm_nopm": tpm_nopm.plot,
    # "latency": generate_latency,
    "cpu_utilization": cpu_utilization.plot,
    "dirty_buffers": dirty_buffers.plot,
}

def main(result_dirs):
    for resdir in result_dirs:
        if not os.path.isdir(resdir):
            print(f"Directory not found: {resdir}", file=sys.stderr)
            sys.exit(1)

        os.chdir(resdir)

        # 生成 SIMPLE_GRAPHS 图表
        for graph in SIMPLE_GRAPHS:
            print(f"Generating {resdir}/{graph}.png ... ", end="")
            try:
                graph_func_map[graph](WIDTH, HEIGHT)
                print("OK")
            except Exception as e:
                print("ERROR")
                print(e, file=sys.stderr)
                sys.exit(3)

        # blk 设备图
        for fname in glob.glob("data/blk_*.csv"):
            devname = os.path.basename(fname).replace(".csv", "")
            print(f"Generating {resdir}/{devname}_iops.png ... ", end="")
            try:
                blk_device_iops.plot(devname,WIDTH,HEIGHT)
                print("OK")
            except Exception as e:
                print("ERROR")
                print(e, file=sys.stderr)
                sys.exit(3)

            print(f"Generating {resdir}/{devname}_kbps.png ... ", end="")
            try:
                blk_device_kbps.plot(devname,WIDTH,HEIGHT)
                print("OK")
            except Exception as e:
                print("ERROR")
                print(e, file=sys.stderr)
                sys.exit(3)

        # # net 设备图
        # for fname in glob.glob("data/net_*.csv"):
        #     devname = os.path.basename(fname).replace(".csv", "")
        #     print(f"Generating {resdir}/{devname}_iops.png ... ", end="")
        #     try:
        #         generate_net_device_iops(resdir, devname, WIDTH, HEIGHT)
        #         print("OK")
        #     except Exception as e:
        #         print("ERROR")
        #         print(e, file=sys.stderr)
        #         sys.exit(3)

        #     print(f"Generating {resdir}/{devname}_kbps.png ... ", end="")
        #     try:
        #         generate_net_device_kbps(resdir, devname, WIDTH, HEIGHT)
        #         print("OK")
        #     except Exception as e:
        #         print("ERROR")
        #         print(e, file=sys.stderr)
        #         sys.exit(3)

        os.chdir("..")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} RESULT_DIR [...]", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1:])
