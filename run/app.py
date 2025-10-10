import os
import re
import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import time
from typing import Optional
from fastapi.templating import Jinja2Templates
from functools import cmp_to_key

def natural_compare(a, b):
    a_name = a["name"]
    b_name = b["name"]

    # 把字符串分割成数字和非数字部分
    pattern = re.compile(r'(\d+|\D+)')
    parts_a = pattern.findall(a_name)
    parts_b = pattern.findall(b_name)

    for pa, pb in zip(parts_a, parts_b):
        if pa.isdigit() and pb.isdigit():
            # 数字部分按数值比较
            if int(pa) < int(pb):
                return -1
            elif int(pa) > int(pb):
                return 1
        else:
            # 非数字部分按字符串比较
            if pa < pb:
                return -1
            elif pa > pb:
                return 1
    # 长度不同时，短的排在前
    return len(parts_a) - len(parts_b)
app = FastAPI(title="BenchmarkSQL TPCC Report Viewer")

# 定义报告文件夹的正则表达式
REPORT_DIR_PATTERN = re.compile(r"^my_result_\d{4}-\d{2}-\d{2}_\d{6}$")

def find_max_jvm_memory(log_file):
    max_memory = None
    if not os.path.exists(log_file):
        return None
    with open(log_file, 'r') as f:
        for line in f:
            match = re.search(r'JVM Max Memory:\s*(\d+)MB', line)
            if match:
                max_memory = int(match.group(1))
                break
    return max_memory

def find_report_dirs(root="."):
    """
    递归查找所有符合条件的报告文件夹，并构建树形结构
    """
    # 存储所有符合条件的目录路径
    report_paths = []
    
    # 递归遍历目录
    for dirpath, _, filenames in os.walk(root):
        # 检查当前目录是否符合报告文件夹模式
        dirname = os.path.basename(dirpath)
        if REPORT_DIR_PATTERN.match(dirname):
            # 提取日期时间
            try:
                date_str = dirname.split("my_result_",)[1]
                date_time = datetime.datetime.strptime(date_str, "%Y-%m-%d_%H%M%S")
                report_paths.append({
                    "path": dirpath,
                    "name": dirname,
                    "datetime": date_time
                })
            except ValueError:
                print(f"日期时间解析失败: {dirname}")
    
    # 按日期时间排序，最新的在前
    report_paths.sort(key=lambda x: x["datetime"], reverse=True)
    
    # 构建树形结构
    tree = []
    for report in report_paths:
        parts = report["path"].split(os.sep)
        # 如果是Windows系统，去掉盘符部分
        if os.name == "nt" and re.match(r'^[A-Za-z]:', parts[0]):
            parts = parts[1:]
            
        current_level = tree
        for i, part in enumerate(parts):
            # 查找当前层级中是否已存在同名节点
            existing_node = next((n for n in current_level if n["name"] == part), None)
            
            if i == len(parts) - 1:
                # 叶子节点（报告文件夹）
                if not existing_node:
                    max_jvm_memory = find_max_jvm_memory(os.path.join(report["path"], 'benchmarksql-debug.log'))
                    if max_jvm_memory is not None:
                        # 找到对应的内存节点
                        max_jvm_node = next((n for n in current_level if n["name"] == max_jvm_memory), None)
                        if max_jvm_node is not None:
                            max_jvm_node["children"].append({
                                "name": part,
                                "path": report["path"],
                                "datetime": report["datetime"]
                            })
                        else:
                            new_memory_node = {
                                "name": max_jvm_memory,
                                "children": [{
                                    "name": part,
                                    "path": report["path"],
                                    "datetime": report["datetime"]
                                }]
                            }
                            current_level.append(new_memory_node)
                    else:
                        current_level.append({
                            "name": part,
                            "path": report["path"],
                            "datetime": report["datetime"]
                        })
            else:
                # 中间节点（普通文件夹）
                if not existing_node:
                    new_node = {
                        "name": part,
                        "children": []
                    }
                    current_level.append(new_node)
                    current_level = new_node["children"]
                else:
                    current_level = existing_node["children"]
    
    return tree[0]['children'] if tree else {}

# 获取最新的报告文件夹
def get_latest_report_dir():
    reports = find_report_dirs()
    return reports[0]["name"] if reports else None

# 设置静态文件目录
# app.mount("/reports", StaticFiles(directory="."), name="reports")

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 报告列表 API
@app.get("/api/reports")
async def get_reports():
    reports = find_report_dirs()
    # reports.sort(key=cmp_to_key(natural_compare), reverse=True)
    return reports

ROOT = Path(".").resolve()  # 从当前工作目录查找 my_result_* 文件夹
FOLDER_PATTERN = re.compile(r"^my_result_\d{4}-\d{2}-\d{2}_\d{6}$")  # 严格匹配类似 my_result_2025-09-23_153737

@app.get("/reports/{folder}/{file_path:path}")
async def serve_report_file(folder: str, file_path: str, request: Request):
    """
    安全地返回 folder 下的文件。只允许匹配 FOLDER_PATTERN 的文件夹名，
    并且必须存在于当前工作目录的直接子目录中。
    """
    # if not FOLDER_PATTERN.match(folder):
    #     raise HTTPException(status_code=400, detail="invalid folder")
    target_dir = ROOT / folder
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail="folder not found")
    # 构造目标文件并解析为绝对路径，防止路径穿越
    target = (target_dir / file_path).resolve()
    # 必须保证 target 在 target_dir 内
    try:
        target.relative_to(target_dir.resolve())
    except Exception:
        raise HTTPException(status_code=403, detail="forbidden")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    # 使用 FileResponse 返回
    return FileResponse(path=str(target))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
