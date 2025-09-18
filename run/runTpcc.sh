#!/usr/bin/env bash

# 运行基准测试
echo "开始运行基准测试..."


# 默认配置
props_file="./props.opengauss.1000w"
run_count=1  # 默认运行1次
destroy_db=0
# 远程服务器信息 - 请根据实际情况修改以下信息
remote_server="shuaikangzhou@127.0.0.1 -p 2222"  
# 远程服务器用户名和主机地址，例如：root@192.168.1.100，需要与本机设置互信


# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        # 短参数带值：-c 或 --config 后面跟配置文件路径
        -a)
            props_file="./props.opengauss.atf"
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
        # 帮助信息
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo "  -a, --atf    指定配置文件路径（默认: ./props.opengauss.atf）"
            echo "  -n           指定运行次数（默认: 1，需要跟一个正整数）"
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

# 循环运行基准测试
for ((i=1; i<=run_count; i++)); do
    echo "===== 开始第 $i 次基准测试 ====="
    echo "配置文件: $props_file"

    # 登录远程服务器启动数据库
    echo "登录远程服务器 $remote_server 启动数据库..."
    ssh $remote_server "openGauss start"
    
    # 等待10秒让数据库完全启动
    echo "等待10秒让数据库启动完成..."
    sleep 10

    # 重建数据仓
    if [ "$destroy_db" -eq 1 ]; then
        ./runDatabaseDestroy.sh "$props_file"
        ./runDatabaseBuild.sh "$props_file"
    fi

    ./runBenchmark.sh "$props_file"

     # 登录远程服务器关闭数据库
    echo "登录远程服务器 $remote_server 关闭数据库..."
    ssh $remote_server "openGauss stop"
    
    # 等待10秒让数据库完全关闭
    echo "等待10秒让数据库关闭完成..."
    # sleep 10

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

    echo "===== 第 $i 次基准测试完成 ====="
    echo
done

echo "所有 $run_count 次任务完成！"