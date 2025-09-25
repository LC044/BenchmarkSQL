#!/usr/bin/env bash

if [ $# -eq 0 ] ; then
    echo "usage: $(basename $0) PROPS_FILE" >&2
    exit 2
fi

# 设置JVM内存参数，默认最大内存4000MB，初始内存为最大内存的一半 
# 从用户输入的参数里读取JVM内存设置（如果有的话）例如：-m 400
# 解析命令行参数
jvm_max_mem=4000  # 默认最大内存4000MB
PROPS_FILE=$1
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                jvm_max_mem=$2
                shift 2
            else
                echo "错误：-m 后面需要跟一个正整数" >&2
                exit 1
            fi
            ;;
        # 未知参数，跳过
        *)
            PROPS_FILE=$1
            shift
            ;;
    esac
done

# 运行序列号文件
SEQ_FILE="./.jTPCC_run_seq.dat"
if [ ! -f "${SEQ_FILE}" ] ; then
    echo "0" > "${SEQ_FILE}"
fi
SEQ=$(expr $(cat "${SEQ_FILE}") + 1) || exit 1
echo "${SEQ}" > "${SEQ_FILE}"

source ./funcs.sh "${PROPS_FILE}"

setCP || exit 1

myOPTS="-Dprop=${PROPS_FILE} -DrunID=${SEQ}"

jvm_initial_mem=$((jvm_max_mem / 2))

echo "运行 jTPCC: 初始内存 ${jvm_initial_mem}MB, 最大内存 ${jvm_max_mem}MB"

# 根据jvm_max_mem的值决定是否设置JVM内存参数
if [ "${jvm_max_mem}" -le 0 ] ; then
    java -Xms${jvm_initial_mem}m -Xmx${jvm_max_mem}m -cp "$myCP" $myOPTS jTPCC
else
    java -cp "$myCP" $myOPTS jTPCC
fi


