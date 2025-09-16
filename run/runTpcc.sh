#!/usr/bin/env bash

# 运行基准测试
echo "开始运行基准测试..."


# 默认配置
props_file="./props.opengauss.1000w"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        # 短参数带值：-c 或 --config 后面跟配置文件路径
        -a)
            props_file="./props.opengauss.atf"
            shift
            ;;
        # 帮助信息
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo "  -a, --atf    指定配置文件路径（默认: ./props.opengauss.atf）"
            exit 0
            ;;
            
        # 未知参数
        *)
            echo "错误：未知参数 $1" >&2
            echo "使用 -h 或 --help 查看帮助" >&2
            exit 1
            ;;
    esac
done

# 运行基准测试
echo "开始运行基准测试..."
echo "配置文件: $props_file"
./runBenchmark.sh $props_file

# 从当前文件夹中查找最新的my_result_*文件夹
echo "查找最新的结果文件夹..."
result_dir=$(find . -maxdepth 1 -type d -name "my_result_*" -printf "%T+ %p\n" | sort -r | head -n 1 | cut -d' ' -f2-)

if [ -z "$result_dir" ]; then
    echo "错误：未找到任何my_result_*文件夹"
    exit 1
fi

# 去除可能的./前缀
result_dir=$(basename "$result_dir")

echo "使用最新的结果文件夹：$result_dir"

# 生成图表
echo "生成测试图表..."
./generateGraphs.sh "$result_dir/"

# 移动日志文件到结果文件夹
echo "移动日志文件..."
if [ -f "./benchmarksql-debug.log" ]; then
    mv ./benchmarksql-debug.log "$result_dir/"
else
    echo "警告：未找到benchmarksql-debug.log文件"
fi

# 运行内存分析脚本
echo "运行内存分析..."
if [ -f "$result_dir/benchmarksql-debug.log" ]; then
    python3 ./misc/memory.py "$result_dir/benchmarksql-debug.log"
else
    echo "错误：在结果文件夹中未找到benchmarksql-debug.log"
    exit 1
fi

echo "所有任务完成！"
