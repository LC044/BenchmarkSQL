
#!/usr/bin/env bash

# 运行基准测试
echo "开始运行基准测试..."


# 默认配置
props_file="./props.opengauss"
warehouses=200
enable_atf=0
run_count=1  # 默认运行1次
destroy_db=0

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -a)
            enable_atf=1
            shift
            ;;
        # 运行次数参数
        -n)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                run_count=$2
                shift 2
            else
                echo "错误：-n 后面需要跟一个正整数" >&2
                exit 1
            fi
            ;;
        -c)
            destroy_db=1
            shift
            ;;
        -w)
            # 判断参数是否是200、400、1000中的任意一个
            if [ "$2" -eq 200 ] || [ "$2" -eq 400 ] || [ "$2" -eq 1000 ]; then
                warehouses=$2
                shift 2
            else
                echo "参数 -w 必须是200、400、1000中的任何一个"
                exit 1
            fi
            ;;
        # 帮助信息
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo "  -a    启用ATF功能"
            echo "  -n    指定运行次数（默认: 1，需要跟一个正整数）"
            echo "  -c    每次运行前销毁并重建数据库"
            echo "  -w    指定仓库数量（200、400、1000）"
            echo "  -h, --help   显示帮助信息"
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

# 检查运行次数是否有效
if [[ $run_count -lt 1 ]]; then
    echo "错误：运行次数必须大于0" >&2
    exit 1
fi

props_file="./props.opengauss.${warehouses}w"
if [ "$enable_atf" -eq 1 ]; then
    props_file="${props_file}.atf"
fi

source ./server.sh "$warehouses"

function generateGraphs() {
    echo "生成图表..."
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
    python3 ./generateGraphs.py "$result_dir/"

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
}

# 循环运行基准测试
for ((i=1; i<=run_count; i++)); do
    echo "===== 开始第 $i 次基准测试 ====="
    echo "配置文件: $props_file"
    # 如果启用了销毁数据库选项，则重建数据库
    if [ "$destroy_db" -eq 1 ]; then
        rebuild_database # 重建数据库
    fi

    start_database # 启动数据库
    ./runBenchmark.sh "$props_file" 
    stop_database # 关闭数据库
    generateGraphs # 生成图表
    echo "===== 第 $i 次基准测试完成 ====="
    echo
done

echo "所有 $run_count 次任务完成！"
