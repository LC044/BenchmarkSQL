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

app = FastAPI(title="BenchmarkSQL TPCC Report Viewer")

# 定义报告文件夹的正则表达式
REPORT_DIR_PATTERN = re.compile(r"^my_result_\d{4}-\d{2}-\d{2}_\d{6}$")

# 找到所有测试报告文件夹
def find_report_dirs(root="."):
    dirs = []
    for name in os.listdir(root):
        if os.path.isdir(name) and REPORT_DIR_PATTERN.match(name):
            # 从文件夹名中提取日期时间
            date_str = name.split("my_result_",)[1]
            print(date_str)
            try:
                date_time = datetime.datetime.strptime(date_str, "%Y-%m-%d_%H%M%S")
                dirs.append({"name": name, "datetime": date_time})
            except ValueError:
                print("日期时间解析失败:", date_str)
                continue
    # 按日期时间排序，最新的在前
    return sorted(dirs, key=lambda x: x["datetime"], reverse=True)

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
    return [{"name": r["name"], "datetime": r["datetime"].isoformat()} for r in reports]

ROOT = Path(".").resolve()  # 从当前工作目录查找 my_result_* 文件夹
FOLDER_PATTERN = re.compile(r"^my_result_\d{4}-\d{2}-\d{2}_\d{6}$")  # 严格匹配类似 my_result_2025-09-23_153737

@app.get("/reports/{folder}/{file_path:path}")
async def serve_report_file(folder: str, file_path: str, request: Request):
    """
    安全地返回 folder 下的文件。只允许匹配 FOLDER_PATTERN 的文件夹名，
    并且必须存在于当前工作目录的直接子目录中。
    """
    if not FOLDER_PATTERN.match(folder):
        raise HTTPException(status_code=400, detail="invalid folder")
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
