
#!/usr/bin/env bash

warehouses=$1

# 远程服务器信息 - 请根据实际情况修改以下信息

remote_server="zhousk@192.168.200.209"

# 远程服务器用户名和主机地址，例如：root@192.168.1.100，需要与本机设置互信

db_dir="/mnt/nvme2n1/zhousk/data/data_n1"
TABSPACE2_DIR="/mnt/nvme3n1/zhousk/data/data_n1"
TABSPACE3_DIR="/mnt/nvme4n1/zhousk/data/data_n1"

XLOG_DIR="/mnt/raid0/zhousk/data/data_n1/pg_xlog"

backup_dir="/mnt/nvme4n1/zhousk/backup/${warehouses}w"


# mv $DATA_DIR/pg_location/tablespace2 $TABSPACE2_DIR/tablespace2 
# cd $DATA_DIR/pg_location/ 
# ln -svf $TABSPACE2_DIR/tablespace2 ./


function rebuild_database() {
    echo "销毁并重建数据库..."
    echo "删除数据库文件... ${db_dir}/"
    ssh $remote_server "rm -rf $db_dir"
    ssh $remote_server "rm -rf $TABSPACE2_DIR/tablespace2"
    ssh $remote_server "rm -rf $TABSPACE3_DIR/tablespace3"
    ssh $remote_server "rm -rf $XLOG_DIR"
    # 恢复数据库文件
    echo "恢复数据库文件... from ${backup_dir} to ${db_dir}"
    ssh $remote_server "cp -r $backup_dir $db_dir/"
    # 对数据进行分盘
    echo "对数据进行分盘..."
    ssh $remote_server "mv ${db_dir}/pg_location/tablespace2 ${TABSPACE2_DIR}/tablespace2"
    ssh $remote_server "mv ${db_dir}/pg_location/tablespace3 ${TABSPACE3_DIR}/tablespace3"
    ssh $remote_server "mv ${db_dir}/pg_xlog ${XLOG_DIR}"
    # 创建符号链接
    echo "创建符号链接..."
    ssh $remote_server "ln -svf $TABSPACE2_DIR/tablespace2 ${db_dir}/pg_location/"
    ssh $remote_server "ln -svf $TABSPACE3_DIR/tablespace3 ${db_dir}/pg_location/"
    ssh $remote_server "ln -svf $XLOG_DIR ${db_dir}"
    echo "数据库重建完成."
}

function start_database() {
    echo "启动数据库..."
    ssh $remote_server "gs_ctl start -D $db_dir -Z single_node -l logfil"
    echo "等待10s..."
    sleep 10  # 等待10秒让数据库完全启动
}

function stop_database() {
    echo "关闭数据库..."
    ssh $remote_server "gs_ctl stop -D $db_dir"
}