#!/bin/sh

if [ $# -ne 1 ] ; then
    echo "usage: $(basename $0) RESULT_DIR" >&2
    exit 2
fi

TABLE_WIDTH="1100px"

function getRunInfo()
{
    exec 3< data/runInfo.csv
    read hdrs <&3
    hdrs=$(echo ${hdrs} | tr ',' ' ')
    IFS=, read $hdrs <&3
    exec <&3-

    eval echo "\$$1"
}

function getRunInfoColumns()
{
    exec 3< data/runInfo.csv
    read hdrs <&3
    hdrs=$(echo ${hdrs} | tr ',' ' ')
    exec <&3-

    echo "${hdrs}"
}

function getProp()
{
    grep "^${1}=" run.properties | sed -e "s/^${1}=//"
}

#./generateGraphs.sh "${1}"

# python3 ./generateGraphs.py "${1}"

cd "${1}"
echo -n "Generating ${1}/report.html ... "

# ----
# Start the report.
# ----
cat >report.html <<_EOF_
<html>
<head>
  <title>
    BenchmarkSQL Run #$(getRunInfo run) started $(getRunInfo sessionStart)
  </title>
  <style>

h1,h2,h3,h4	{ color:#2222AA;
		}

h1		{ font-family: Helvetica,Arial;
		  font-weight: 700;
		  font-size: 24pt;
		}

h2		{ font-family: Helvetica,Arial;
		  font-weight: 700;
		  font-size: 18pt;
		}

h3,h4		{ font-family: Helvetica,Arial;
		  font-weight: 700;
		  font-size: 16pt;
		}

p,li,dt,dd	{ font-family: Helvetica,Arial;
		  font-size: 14pt;
		}

p		{ margin-left: 50px;
		}

pre		{ font-family: Courier,Fixed;
		  font-size: 14pt;
		}

samp		{ font-family: Courier,Fixed;
		  font-weight: 900;
		  font-size: 14pt;
		}

big		{ font-weight: 900;
		  font-size: 120%;
		}
img {
  width: 1200px;
  height: 400px;
}
  </style>
</head>
<body bgcolor="#ffffff">
  <h1>
    BenchmarkSQL Run #$(getRunInfo run) started $(getRunInfo sessionStart)
  </h1>

  <p>
    This TPC-C style benchmark run was performed by the "$(getRunInfo driver)"
    driver of BenchmarkSQL version $(getRunInfo driverVersion). 
  </p>
_EOF_

# ----
# Show the run properties.
# ----
cat >>report.html <<_EOF_
  <h2>
    Run Properties
  </h2>
  <p>
    <table width="${TABLE_WIDTH}" border="0">
    <tr><td bgcolor="#f0f0f0">
    <pre><small>
_EOF_
sed -e 's/^password=.*/password=\*\*\*\*\*\*/' <run.properties >>report.html
cat >>report.html <<_EOF_
    </small></pre>
    </td></tr>
    </table>
  </p>

_EOF_

# ----
# Show the result summary.
# ----
cat >>report.html <<_EOF_
  <h2>
    Result Summary
  </h2>
_EOF_

if [ $(getRunInfo driver) == "simple" ] ; then
    cat >> report.html <<_EOF_
    <p>
      Note that the "simple" driver is not a true TPC-C implementation.
      This driver only measures the database response time, not the
      response time of a System under Test as it would be experienced
      by an end-user in a 3-tier test implementation.
    </p>
_EOF_
fi

cat >> report.html <<_EOF_
  <p>
    <table width="${TABLE_WIDTH}" border="2">
    <tr>
      <th rowspan="2" width="16%"><b>Transaction<br/>Type</b></th>
      <th colspan="2" width="24%"><b>Latency</b></th>
      <th rowspan="2" width="12%"><b>Count</b></th>
      <th rowspan="2" width="12%"><b>Percent</b></th>
      <th rowspan="2" width="12%"><b>Rollback</b></th>
      <th rowspan="2" width="12%"><b>Errors</b></th>
      <th rowspan="2" width="12%"><b>Skipped<br/>Deliveries</b></th>
    </tr>
    <tr>
      <th width="12%"><b>90th&nbsp;%</b></th>
      <th width="12%"><b>Maximum</b></th>
    </tr>
_EOF_

tr ',' ' ' <data/tx_summary.csv | \
    while read name count percent ninth max limit rbk error dskipped ; do
	[ ${name} == "tx_name" ] && continue
	[ ${name} == "tpmC" ] && continue
	[ ${name} == "tpmTotal" ] && continue

	echo "    <tr>"
	echo "      <td align=\"left\">${name}</td>"
	echo "      <td align=\"right\">${ninth}</td>"
	echo "      <td align=\"right\">${max}</td>"
	echo "      <td align=\"right\">${count}</td>"
	echo "      <td align=\"right\">${percent}</td>"
	echo "      <td align=\"right\">${rbk}</td>"
	echo "      <td align=\"right\">${error}</td>"
	echo "      <td align=\"right\">${dskipped}</td>"
	echo "    </tr>"
    done >>report.html

tpmC=$(grep "^tpmC," data/tx_summary.csv | sed -e 's/[^,]*,//' -e 's/,.*//')
tpmCpct=$(grep "^tpmC," data/tx_summary.csv | sed -e 's/[^,]*,[^,]*,//' -e 's/,.*//')
tpmTotal=$(grep "^tpmTotal," data/tx_summary.csv | sed -e 's/[^,]*,//' -e 's/,.*//')
cat >>report.html <<_EOF_
    </table>
  </p>

  <p>
    <table border="0">
      <tr>
        <td align="left"><big><b>Overall tpmC:</b></big></td>
        <td align="right"><big><b>${tpmC}</b></big></td>
      </tr>
      <tr>
        <td align="left"><big><b>Overall tpmTotal:</b></big></td>
        <td align="right"><big><b>${tpmTotal}</b></big></td>
      </tr>
    </table>
  </p>
  <p>
    The TPC-C specification has an theoretical maximum of 12.86 NEW_ORDER
    transactions per minute per warehouse. In reality this value cannot
    be reached because it would require a perfect mix with 45% of NEW_ORDER
    transactions and a ZERO response time from the System under Test
    including the database. 
  </p>
  <p>
    The above tpmC of ${tpmC} is ${tpmCpct} of that theoretical maximum for a
    database with $(getRunInfo runWarehouses) warehouses.
  </p>

_EOF_

# ----
# Show the graphs for tpmC/tpmTOTAL and latency.
# ----
cat >>report.html <<_EOF_
  <h2>
    Transactions per Minute and Transaction Latency
  </h2>
  <p>
    tpmC is the number of NEW_ORDER Transactions, that where processed
    per minute. tpmTOTAL is the number of Transactions processed per
    minute for all transaction types, but without the background part
    of the DELIVERY transaction. 

    <br/>
    <img src="tpm_nopm.png"/>
    <br/>
    <img src="latency.png"/>
  </p>
_EOF_

# ------------- 新增：提取 benchmark-debug.log 中的内存数据 -------------
# 定义日志路径（假设日志在结果目录 ${1} 下，若路径不同需调整）
DEBUG_LOG="benchmarksql-debug.log"

# 初始化内存变量（若日志不存在，默认显示 "N/A"）
MEM_MAX_USED="N/A"
MEM_MAX_TOTAL="N/A"
MEM_MIN_USED="N/A"
MEM_MIN_TOTAL="N/A"
MEM_MAXMIN_USED="N/A"
MEM_MAXMIN_TOTAL="N/A"
MEM_AVG_USED="N/A"
MEM_AVG_TOTAL="N/A"
JVM_MAX_MEM="N/A"
AVERAGE_PERIOD="N/A"

# 检查日志文件是否存在，存在则提取数据
if [ -f "${DEBUG_LOG}" ]; then
    # 提取最大内存：Max memory usage: 1862MB / 2041MB → 取第4列（已用）、第6列（总）
    MEM_MAX_USED=$(grep "Max memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $4}' | sed 's/MB$//')
    MEM_MAX_TOTAL=$(grep "Max memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $6}' | sed 's/MB$//')
    
    # 提取最小内存：Min memory usage: 45MB / 1963MB → 取第4列（已用）、第6列（总）
    MEM_MIN_USED=$(grep "Min memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $4}' | sed 's/MB$//')
    MEM_MIN_TOTAL=$(grep "Min memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $6}' | sed 's/MB$//')
    
    # 提取最大-最小内存差值：Max-min memory usage: 1817MB / 78MB → 取第5列（已用差值）、第7列（总差值）
    MEM_MAXMIN_USED=$(grep "Max-min memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $4}' | sed 's/MB$//')
    MEM_MAXMIN_TOTAL=$(grep "Max-min memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $6}' | sed 's/MB$//')
    
    # 提取平均内存：Average memory usage: 967MB / 2040MB → 取第5列（已用平均）、第7列（总平均）
    MEM_AVG_USED=$(grep "Average memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $4}' | sed 's/MB$//')
    MEM_AVG_TOTAL=$(grep "Average memory usage" "${DEBUG_LOG}" | tail -n 1  | awk '{print $6}' | sed 's/MB$//')

    # 提取JVM最大内存设置：JVM Max Memory: 4000MB → 取第4列
    JVM_MAX_MEM=$(grep "JVM Max Memory" "${DEBUG_LOG}" | tail -n 1 | awk '{print $4}' | sed 's/MB$//')

    # 提取平均周期：Average period: 2.50 minutes → 取第3列
    AVERAGE_PERIOD=$(grep "Average period" "${DEBUG_LOG}" | tail -n 1 | awk '{print $3}' | sed 's/ minutes$//')
else
    # 日志不存在时，输出警告（仅打印到控制台，不影响报告生成）
    echo "Warning: ${DEBUG_LOG} not found, memory stats will show 'N/A' in report." >&2
fi
# ----------------------------------------------------------------------



# ----
# Add all the System Resource graphs. First the CPU and dirty buffers.
# ----
cat >>report.html <<_EOF_
  <h2>
    System Resource Usage
  </h2>
  <h3>
    Memory Usage of the Benchmark Client
  </h3>
  <p>
    The memory usage of the Benchmark Client as measured by the logger.
    The JVM was started with a maximum heap size of <b>${JVM_MAX_MEM}MB</b>.
    <br/>
    <img src="memory_usage_curve.png"/>
  </p>
  <p>
    <b>Memory Usage Statistics:</b>
    <table width="${TABLE_WIDTH}" border="2" class="mem-table">
      <tr>
        <th rowspan="2"><b>Memory Metric</b></th>
        <th colspan="2"><b>Memory Usage</b></th>
      </tr>
      <tr>
        <th><b>Used (MB)</b></th>
        <th><b>Total (MB)</b></th>
      </tr>
      <tr>
        <td align="left"><b>Maximum</b></td>
        <td align="right">${MEM_MAX_USED}</td>
        <td align="right">${MEM_MAX_TOTAL}</td>
      </tr>
      <tr>
        <td align="left"><b>Minimum</b></td>
        <td align="right">${MEM_MIN_USED}</td>
        <td align="right">${MEM_MIN_TOTAL}</td>
      </tr>
      <tr>
        <td align="left"><b>Max - Min (Difference)</b></td>
        <td align="right">${MEM_MAXMIN_USED}</td>
        <td align="right">${MEM_MAXMIN_TOTAL}</td>
      </tr>
      <tr>
        <td align="left"><b>Average</b></td>
        <td align="right">${MEM_AVG_USED}</td>
        <td align="right">${MEM_AVG_TOTAL}</td>
      </tr>
      <tr>
        <th rowspan="2" align="left"><b>Average period(minutes)</b></th>
        <th colspan="2"><b>${AVERAGE_PERIOD}</b></th>
      </tr>
    </table>
  </p>
  <h3>
    CPU Utilization
  </h3>
  <p>
    The percentages for User, System and IOWait CPU time are stacked
    on top of each other. 

    <br/>
    <img src="cpu_utilization.png"/>
  </p>

  <h3>
    Dirty Kernel Buffers
  </h3>
  <p>
    We track the number of dirty kernel buffers, as measured by
    the "nr_dirty" line in /proc/vmstat, to be able to correlate
    IO problems with when the kernel's IO schedulers are flushing
    writes to disk. A write(2) system call does not immediately
    cause real IO on a storage device. The data written is just
    copied into a kernel buffer. Several tuning parameters control
    when the OS is actually transferring these dirty buffers to
    the IO controller(s) in order to eventually get written to
    real disks (or similar). 

    <br/>
    <img src="dirty_buffers.png"/>
  </p>
_EOF_

# ----
# Add all the block device IOPS and KBPS
# ---
for devdata in data/blk_*.csv ; do
    if [ ! -f "$devdata" ] ; then
        break
    fi

    dev=$(basename ${devdata} .csv)
    cat >>report.html <<_EOF_
    <h3>
      Block Device ${dev}
    </h3>
    <p>
      <img src="${dev}_iops.png"/>
      <br/>
      <img src="${dev}_kbps.png"/>
    </p>
_EOF_
done

# ----
# Add all the network device IOPS and KBPS
# ---
for devdata in data/net_*.csv ; do
    if [ ! -f "$devdata" ] ; then
        break
    fi

    dev=$(basename ${devdata} .csv)
    cat >>report.html <<_EOF_
    <h3>
      Network Device ${dev}
    </h3>
    <p>
      <img src="${dev}_iops.png"/>
      <br/>
      <img src="${dev}_kbps.png"/>
    </p>
_EOF_
done

# ----
# Finish the document.
# ----
cat >>report.html <<_EOF_
</body>
</html>

_EOF_

echo "OK"
