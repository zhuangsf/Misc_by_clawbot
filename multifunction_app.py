#!/usr/bin/env python3
"""
统一多功能应用 - 集成所有功能到8080端口
包含：市场监控、K线图表、AI参数查看器
"""

import os
import sys
import json
import time
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, send_file, render_template_string, request
from flask_cors import CORS

# 添加到系统路径，便于导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # 允许跨域

# ==================== 配置区域 ====================
CONFIG = {
    "PORT": 8080,
    "DEBUG": True,
    
    # 市场监控相关配置
    "MARKET_MONITOR": {
        "LOG_FILES": {
            "eth": "/root/.openclaw/workspace/eth_swap_monitor.log",
            "xau": "/root/.openclaw/workspace/xau_swap_monitor.log",
        },
        "CACHE_TIME": 30,  # 数据缓存时间（秒）
    },
    
    # 静态文件目录
    "STATIC_PATHS": {
        "ai_params_viewer": "/root/.openclaw/workspace/ai-params-viewer",
        "charts_fixed": "/root/.openclaw/workspace/charts_fixed",
    },
}

# 数据缓存
DATA_CACHE = {
    "eth": {"data": None, "timestamp": None},
    "xau": {"data": None, "timestamp": None},
    "alerts": {"data": None, "timestamp": None},
}

# 导入放量记录数据库模块
try:
    from volume_spikes_db import (
        get_records as db_get_records,
        add_record as db_add_record,
        get_statistics as db_get_statistics,
        init_db as db_init
    )
    USE_SQLITE = True
    # 初始化数据库
    db_init()
except ImportError:
    USE_SQLITE = False
    print("⚠️ SQLite模块不可用，将使用文件存储")

# ==================== 市场监控功能 ====================
def parse_latest_data(log_file, symbol_name):
    """解析最新监控数据"""
    if not os.path.exists(log_file):
        return {
            "status": "error",
            "message": f"日志文件不存在: {log_file}",
            "symbol": symbol_name,
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return {
                "status": "empty",
                "symbol": symbol_name,
                "timestamp": datetime.now().isoformat()
            }
        
        # 从最后200行中查找最新数据（增加搜索范围以找到状态信息）
        recent_lines = lines[-200:] if len(lines) > 200 else lines
        recent_lines.reverse()
        
        latest_data = {
            "symbol": symbol_name,
            "timestamp": datetime.now().isoformat(),
            "price": None,
            "current_volume": None,
            "previous_volume": None,
            "current_volume_usdt": None,
            "previous_volume_usdt": None,
            "volume_ratio": None,
            "status": "unknown",
            "last_check_time": None,
            "running_time": None,
            "check_count": 0,
            "alert_count": 0,
        }
        
        # 获取实时价格（从OKX API）
        try:
            import requests
            if "ETH" in symbol_name:
                ticker_url = "https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT-SWAP"
            else:
                ticker_url = "https://www.okx.com/api/v5/market/ticker?instId=XAU-USDT-SWAP"
            
            response = requests.get(ticker_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    latest_data["price"] = float(data['data'][0]['last'])
        except Exception as e:
            print(f"获取价格失败: {e}")
            # 使用默认价格
            latest_data["price"] = 2123.75 if "ETH" in symbol_name else 5144.70
        
        # 正则表达式匹配
        patterns = {
            "price": r"价格变化.*?([+-]?\d+\.\d+) USDT",
            "current_volume": r"当前成交额: ([\d,\.]+[KM]?) USDT",
            "previous_volume": r"前一成交额: ([\d,\.]+[KM]?) USDT",
            "volume_ratio": r"成交额倍数: ([\d\.]+)倍",
            "check_time": r"当前K线: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            "status": r"状态: (正常|异常)",
        }
        
        # 查找监控状态信息（多行格式）
        # 格式：
        # 🚨 警报次数: 1
        # 🏃 运行时间: 0天 1时0分1秒
        # 🔍 检查次数: 12
        
        # 同时也从 "开始第N次检查..." 推断检查次数（更准确）
        max_check_count = 0
        found_status = False  # 标记是否已找到最新状态
        
        for i, line in enumerate(recent_lines):
            # 从 "开始第N次检查..." 推断检查次数（最准确）
            check_num_match = re.search(r"开始第(\d+)次检查", line)
            if check_num_match:
                check_num = int(check_num_match.group(1))
                if check_num > max_check_count:
                    max_check_count = check_num
            
            # 查找警报次数
            alert_match = re.search(r"警报次数: (\d+)", line)
            if alert_match:
                latest_data["alert_count"] = int(alert_match.group(1))
            
            # 查找运行时间（兼容两种格式，优先解析新的状态行格式）
            # 新格式：📊 状态 | 运行时间: X天 X时 X分 X秒 | 检查次数: X | 警报次数: X
            # 只在未找到状态时才更新（避免旧数据覆盖新数据）
            if not found_status:
                status_match = re.search(r"📊 状态 \| 运行时间: (\d+)天 (\d+)时 (\d+)分 (\d+)秒 \| 检查次数: (\d+) \| 警报次数: (\d+)", line)
                if status_match:
                    days, hours, minutes, seconds, check_cnt, alert_cnt = status_match.groups()
                    latest_data["running_time"] = f"{days}天 {hours}时 {minutes}分 {seconds}秒"
                    latest_data["check_count"] = int(check_cnt)
                    latest_data["alert_count"] = int(alert_cnt)
                    found_status = True  # 找到最新状态后标记
                    # 立即跳出循环，防止后面的旧状态行覆盖数据
                    break
            
            # 旧格式兼容（仅在新格式未匹配时使用）
            if not found_status:
                runtime_match = re.search(r"运行时间: (\d+)天 (\d+)时\s*(\d+)分\s*(\d+)秒", line)
                if runtime_match and not latest_data.get("running_time"):
                    days, hours, minutes, seconds = runtime_match.groups()
                    latest_data["running_time"] = f"{days}天 {hours}时 {minutes}分 {seconds}秒"
                
                # 查找检查次数（作为备选）
                check_match = re.search(r"检查次数: (\d+)", line)
                if check_match and latest_data["check_count"] == 0:
                    check_count = int(check_match.group(1))
                    if check_count > latest_data["check_count"]:
                        latest_data["check_count"] = check_count
        
        # 使用从 "开始第N次检查" 推断的检查次数（仅当新格式未解析到时）
        if max_check_count > 0 and latest_data["check_count"] == 0:
            latest_data["check_count"] = max_check_count
        
        # 查找最新检查数据（多行格式）
        # 格式：
        # [2026-03-05 16:41:28,840] [INFO] 当前K线: 2026-03-05 16:30:00, 成交额: 123.45K USDT
        # [2026-03-05 16:41:28,840] [INFO] 前一K线: 2026-03-05 16:15:00, 成交额: 100.23K USDT
        # [2026-03-05 16:41:28,840] [INFO] 成交额倍数: 1.15倍
        
        def parse_volume_string(vol_str):
            """解析带K/M后缀的成交额字符串"""
            vol_str = vol_str.replace(',', '')
            if vol_str.endswith('M'):
                return float(vol_str[:-1]) * 1_000_000
            elif vol_str.endswith('K'):
                return float(vol_str[:-1]) * 1_000
            else:
                return float(vol_str)
        
        for i, line in enumerate(recent_lines):
            if "当前K线:" in line and "成交额:" in line:
                # 提取当前K线时间和成交额
                time_match = re.search(r"当前K线: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                volume_match = re.search(r"成交额: ([\d,\.]+[KM]?) USDT", line)
                
                if time_match:
                    latest_data["last_check_time"] = time_match.group(1)
                
                if volume_match:
                    try:
                        latest_data["current_volume_usdt"] = parse_volume_string(volume_match.group(1))
                        latest_data["current_volume"] = latest_data["current_volume_usdt"]  # 兼容旧字段
                    except:
                        pass
                
                # 查找前一成交额（可能在下一行）
                for j in range(i-1, max(0, i-5), -1):
                    prev_line = recent_lines[j]
                    if "前一K线:" in prev_line and "成交额:" in prev_line:
                        prev_vol_match = re.search(r"成交额: ([\d,\.]+[KM]?) USDT", prev_line)
                        if prev_vol_match:
                            try:
                                latest_data["previous_volume_usdt"] = parse_volume_string(prev_vol_match.group(1))
                                latest_data["previous_volume"] = latest_data["previous_volume_usdt"]  # 兼容旧字段
                            except:
                                pass
                        break
                
                # 查找成交额倍数（可能在下一行）
                for j in range(i-1, max(0, i-5), -1):
                    ratio_line = recent_lines[j]
                    if "成交额倍数:" in ratio_line:
                        ratio_match = re.search(r"成交额倍数: ([\d\.]+)倍", ratio_line)
                        if ratio_match:
                            latest_data["volume_ratio"] = float(ratio_match.group(1))
                            latest_data["status"] = "异常" if latest_data["volume_ratio"] >= 3 else "正常"
                        break
                
                # 查找价格变化信息（新增）
                for j in range(i-1, max(0, i-6), -1):
                    price_line = recent_lines[j]
                    if "价格变化:" in price_line:
                        # 格式: 价格变化: 2123.50 → 2125.75 USDT (+2.25, +0.11%, 涨)
                        price_match = re.search(r"价格变化: ([\d\.]+) → ([\d\.]+) USDT \(([+-][\d\.]+), ([+-][\d\.]+)%, (涨|跌|平)\)", price_line)
                        if price_match:
                            latest_data["previous_close"] = float(price_match.group(1))
                            latest_data["current_close"] = float(price_match.group(2))
                            latest_data["price_change"] = float(price_match.group(3))
                            latest_data["price_change_percent"] = float(price_match.group(4))
                            latest_data["price_direction"] = price_match.group(5)
                            
                            # 判断放量涨/放量跌
                            ratio = latest_data.get("volume_ratio", 0)
                            direction = latest_data["price_direction"]
                            
                            if ratio >= 2:  # 放量（>=2倍）
                                if direction == "涨":
                                    latest_data["market_status"] = "放量涨 🔥📈"
                                elif direction == "跌":
                                    latest_data["market_status"] = "放量跌 📉⚠️"
                                else:
                                    latest_data["market_status"] = "放量平 📊"
                            else:  # 缩量
                                if direction == "涨":
                                    latest_data["market_status"] = "缩量涨 📈"
                                elif direction == "跌":
                                    latest_data["market_status"] = "缩量跌 📉"
                                else:
                                    latest_data["market_status"] = "缩量平 ➡️"
                        break
                
                break  # 找到最新检查后退出
        
        # 如果没有价格数据，使用默认值
        if latest_data["price"] is None:
            latest_data["price"] = 2123.75 if "ETH" in symbol_name else 5144.70
        
        return latest_data
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"解析日志失败: {str(e)}",
            "symbol": symbol_name,
            "timestamp": datetime.now().isoformat()
        }

def get_today_alerts():
    """获取今日的警报记录（改进版：专业格式显示成交量爆发倍数）"""
    alerts = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for symbol, log_file in CONFIG["MARKET_MONITOR"]["LOG_FILES"].items():
        if not os.path.exists(log_file):
            continue
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 改进：解析检查记录，提取成交量倍数
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # 查找当前K线信息行
                if "当前K线:" in line and "成交额:" in line and today in line:
                    # 修复：日志格式包含毫秒 [2026-03-05 18:27:19,693]
                    time_match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    alert_time = time_match.group(1) if time_match else "未知时间"
                    
                    # 提取当前K线时间
                    kline_time_match = re.search(r"当前K线: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    kline_time = kline_time_match.group(1) if kline_time_match else "未知K线"
                    
                    # 提取当前成交额
                    current_vol_match = re.search(r"成交额: ([\d,\.]+[KM]?) USDT", line)
                    current_volume = current_vol_match.group(1) if current_vol_match else "未知"
                    
                    # 查找前一K线成交额（下一行）
                    previous_volume = "未知"
                    if i + 1 < len(lines) and "前一K线:" in lines[i + 1]:
                        prev_vol_match = re.search(r"成交额: ([\d,\.]+[KM]?) USDT", lines[i + 1])
                        if prev_vol_match:
                            previous_volume = prev_vol_match.group(1)
                    
                    # 查找成交额倍数（可能在 i+2 或 i+3 或 i+4 行，因为中间可能有价格变化行）
                    volume_ratio = None
                    for j in range(i + 2, min(i + 5, len(lines))):
                        if "成交额倍数:" in lines[j]:
                            ratio_match = re.search(r"成交额倍数: ([\d\.]+)倍", lines[j])
                            if ratio_match:
                                volume_ratio = float(ratio_match.group(1))
                            break
                    
                    # 构造专业格式的警报
                    if volume_ratio is not None:
                        if volume_ratio >= 3.0:
                            alert_type = f"成交量爆发 x{volume_ratio:.1f}"
                            alert_level = "high"
                        elif volume_ratio >= 2.0:
                            alert_type = f"成交量放大 x{volume_ratio:.1f}"
                            alert_level = "medium"
                        else:
                            alert_type = f"成交量正常 x{volume_ratio:.1f}"
                            alert_level = "low"
                    else:
                        alert_type = "数据异常"
                        alert_level = "unknown"
                    
                    # 构造消息
                    ratio_str = f"{volume_ratio:.1f}" if volume_ratio is not None else "0.0"
                    message = f"当前K线 {kline_time}: 成交额 {current_volume} USDT, 倍数 x{ratio_str}"
                    
                    alerts.append({
                        "time": alert_time,
                        "kline_time": kline_time,
                        "symbol": "ETH" if symbol == "eth" else "XAU",
                        "type": alert_type,
                        "level": alert_level,
                        "current_volume": current_volume,
                        "previous_volume": previous_volume,
                        "volume_ratio": volume_ratio,
                        "message": message,
                    })
                
                i += 1
                
        except Exception as e:
            print(f"解析警报失败: {e}")
    
    # 按时间倒序排序
    alerts.sort(key=lambda x: x["time"], reverse=True)
    return alerts[:50]  # 返回最近50条

def get_history_data(log_file, symbol_name, limit=20):
    """获取历史成交额数据用于图表展示（只显示已完成的K线）"""
    history = []
    
    if not os.path.exists(log_file):
        return history
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 从日志中提取最近的历史数据
        records = []
        
        # 方法1：从"前一K线"记录中提取（前一K线通常是已完成的）
        # 新格式：前一K线: 2026-03-06 10:15:00, 成交额: 70.84M USDT (已完成)
        # 旧格式：前一K线: 2026-03-06 10:15:00, 成交额: 70.84M USDT
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if "前一K线:" in line and "成交额:" in line:
                # 提取检查时间
                time_match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                check_time = time_match.group(1) if time_match else None
                
                # 提取K线时间
                kline_time_match = re.search(r"前一K线: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                kline_time = kline_time_match.group(1) if kline_time_match else None
                
                # 提取成交额
                vol_match = re.search(r"成交额: ([\d,\.]+[KM]?) USDT", line)
                volume_str = vol_match.group(1) if vol_match else None
                
                # 解析成交额数值
                volume = 0
                if volume_str:
                    volume_str_clean = volume_str.replace(',', '')
                    if volume_str_clean.endswith('M'):
                        volume = float(volume_str_clean[:-1]) * 1_000_000
                    elif volume_str_clean.endswith('K'):
                        volume = float(volume_str_clean[:-1]) * 1_000
                    else:
                        try:
                            volume = float(volume_str_clean)
                        except:
                            pass
                
                # 查找成交额倍数（下一行）
                volume_ratio = 0
                if i + 1 < len(lines) and "成交额倍数:" in lines[i + 1]:
                    ratio_match = re.search(r"成交额倍数: ([\d\.]+)倍", lines[i + 1])
                    if ratio_match:
                        volume_ratio = float(ratio_match.group(1))
                
                if kline_time and volume > 0:
                    records.append({
                        "time": check_time,
                        "kline_time": kline_time,
                        "volume": volume,
                        "volume_str": volume_str,
                        "ratio": volume_ratio,
                        "symbol": symbol_name,
                    })
            
            i += 1
        
        # 去重（按K线时间，保留最后一次记录的值，因为那是完成后的值）
        seen_klines = {}
        for r in records:
            if r["kline_time"]:
                # 保留每个K线时间的最后一条记录（通常是完成后的值）
                seen_klines[r["kline_time"]] = r
        
        # 按时间排序
        unique_records = sorted(seen_klines.values(), key=lambda x: x["kline_time"])
        
        # 返回最近的记录
        return unique_records[-limit:] if len(unique_records) > limit else unique_records
        
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return history

# ==================== 主页面路由 ====================
@app.route('/')
def index():
    """统一入口页面"""
    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🦞 小龙虾多功能平台</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 30px;
                color: #333;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            }
            
            .header {
                text-align: center;
                margin-bottom: 50px;
                padding-bottom: 30px;
                border-bottom: 3px solid #e2e8f0;
            }
            
            .header h1 {
                font-size: 3rem;
                color: #2d3748;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 20px;
            }
            
            .header .subtitle {
                color: #4a5568;
                font-size: 1.2rem;
                opacity: 0.9;
                max-width: 800px;
                margin: 0 auto;
                line-height: 1.6;
            }
            
            .apps-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 30px;
                margin-top: 30px;
            }
            
            .app-card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
                border: 2px solid transparent;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            
            .app-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                border-color: #4299e1;
            }
            
            .app-card h2 {
                font-size: 1.8rem;
                color: #2d3748;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .app-card .emoji {
                font-size: 2rem;
            }
            
            .app-card .description {
                color: #4a5568;
                font-size: 1.1rem;
                line-height: 1.6;
                margin-bottom: 25px;
            }
            
            .app-card .features {
                list-style: none;
                margin-top: 20px;
            }
            
            .app-card .features li {
                padding: 8px 0;
                color: #4a5568;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .app-card .features li:before {
                content: "✅";
                font-size: 0.9rem;
            }
            
            .status-badge {
                display: inline-block;
                padding: 8px 16px;
                background: #48bb78;
                color: white;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: 600;
                margin-top: 15px;
            }
            
            .footer {
                text-align: center;
                margin-top: 50px;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
                color: #718096;
                font-size: 0.9rem;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                .header h1 {
                    font-size: 2.2rem;
                    flex-direction: column;
                    gap: 10px;
                }
                
                .apps-grid {
                    grid-template-columns: 1fr;
                }
                
                .app-card {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    <span class="emoji">🦞</span>
                    小龙虾多功能平台
                    <span class="emoji">🦞</span>
                </h1>
                <p class="subtitle">
                    天才产品庄庄的专用平台 | 统一入口，功能选择 | 专为OKX永续合约监控设计
                </p>
            </div>
            
            <div class="apps-grid">
                <a href="/market_monitor" class="app-card">
                    <h2>
                        <span class="emoji">📊</span>
                        永续合约监控数据查看器
                    </h2>
                    <p class="description">
                        实时监控OKX ETH/XAU永续合约成交量，检测3倍放大异常，查看历史数据和警报记录。
                    </p>
                    <ul class="features">
                        <li>ETH-USDT-SWAP实时监控</li>
                        <li>XAU-USDT-SWAP实时监控</li>
                        <li>15分钟K线成交量分析</li>
                        <li>3倍成交量异常检测</li>
                        <li>实时飞书警报</li>
                        <li>历史数据图表</li>
                    </ul>
                    <div class="status-badge">运行中</div>
                </a>
                
                <a href="/charts_fixed" class="app-card">
                    <h2>
                        <span class="emoji">📈</span>
                        K线图表分析器
                    </h2>
                    <p class="description">
                        查看ETH、BTC、SOL、XAG的K线图表，标注买入卖出点，分析交易历史。
                    </p>
                    <ul class="features">
                        <li>小时线级别K线图</li>
                        <li>买入卖出点标注</li>
                        <li>四种资产对比分析</li>
                        <li>交易历史可视化</li>
                        <li>响应式图表设计</li>
                    </ul>
                    <div class="status-badge">已部署</div>
                </a>
                
                <a href="/ai-params-viewer" class="app-card">
                    <h2>
                        <span class="emoji">🤖</span>
                        AI参数查看器
                    </h2>
                    <p class="description">
                        查看和管理AI模型参数，配置代理设置，优化AI助手性能。
                    </p>
                    <ul class="features">
                        <li>AI参数可视化</li>
                        <li>代理配置管理</li>
                        <li>性能优化工具</li>
                        <li>实时参数调整</li>
                    </ul>
                    <div class="status-badge">已部署</div>
                </a>
                
                <a href="/douyin_emo" class="app-card">
                    <h2>
                        <span class="emoji">🎬</span>
                        抖音共鸣系统视频生成器
                    </h2>
                    <p class="description">
                        为抖音EMO视频号设计的内容生成系统，自动生成15秒情感共鸣视频，支持4种钩子类型。
                    </p>
                    <ul class="features">
                        <li>4种钩子类型自动生成</li>
                        <li>15秒标准短视频</li>
                        <li>AI语音合成（TTS）</li>
                        <li>自动字幕添加</li>
                        <li>批量生成功能</li>
                        <li>文案库预览</li>
                    </ul>
                    <div class="status-badge">已部署</div>
                </a>
            </div>
            
            <div class="footer">
                <p>🦞 小龙虾智能助手 | 为天才产品庄庄定制 | 所有功能统一端口8080</p>
                <p>服务器时间: {{ current_time }} | 访问IP: 120.48.165.67</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(html, current_time=current_time)

# ==================== 市场监控路由 ====================
@app.route('/market_monitor')
def market_monitor_index():
    """市场监控主页面"""
    return send_from_directory('.', 'market_monitor.html')

@app.route('/market_monitor/<path:path>')
def market_monitor_static(path):
    """市场监控静态文件"""
    return send_from_directory('.', path)

@app.route('/volume_spikes')
def volume_spikes_index():
    """放量记录历史页面"""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📈 放量记录查看器 v1.0.1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e4e4e4;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2rem;
            color: #ffd700;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #888;
            font-size: 0.9rem;
        }
        
        .stats-bar {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px 30px;
            border-radius: 10px;
            text-align: center;
            min-width: 150px;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #ffd700;
        }
        
        .stat-label {
            color: #888;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-title {
            font-size: 1.5rem;
            color: #fff;
        }
        
        .filter-tabs {
            display: flex;
            gap: 10px;
        }
        
        .filter-tab {
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.1);
            color: #888;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .filter-tab.active {
            background: #ffd700;
            color: #1a1a2e;
        }
        
        .filter-tab:hover {
            background: rgba(255, 215, 0, 0.3);
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .data-table th {
            color: #888;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        .data-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .volume-high {
            color: #ff6b6b;
            font-weight: bold;
        }
        
        .price-up {
            color: #51cf66;
        }
        
        .price-down {
            color: #ff6b6b;
        }
        
        .symbol-badge {
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .symbol-eth {
            background: rgba(98, 126, 234, 0.2);
            color: #627eea;
        }
        
        .symbol-xau {
            background: rgba(255, 215, 0, 0.2);
            color: #ffd700;
        }
        
        .direction-up {
            color: #51cf66;
        }
        
        .direction-down {
            color: #ff6b6b;
        }
        
        .direction-neutral {
            color: #888;
        }
        
        .timestamp {
            color: #888;
            font-size: 0.85rem;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        
        .empty {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .stats-bar {
                flex-direction: column;
                align-items: center;
            }
            
            .filter-tabs {
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .data-table {
                display: block;
                overflow-x: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="text-align: left; margin-bottom: 15px;">
                <a href="/market_monitor" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: rgba(255, 255, 255, 0.1); border-radius: 25px; color: #fff; text-decoration: none; transition: all 0.3s;">
                    <span>🔙</span>
                    <span>返回监控页面</span>
                </a>
            </div>
            <h1>📈 放量记录查看器</h1>
            <p>记录所有3倍以上放量情况及对应的价格变化 | 数据用于交易策略分析</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value" id="total-count">--</div>
                <div class="stat-label">总记录数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="eth-count">--</div>
                <div class="stat-label">ETH 记录</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="xau-count">--</div>
                <div class="stat-label">XAU 记录</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avg-change">--</div>
                <div class="stat-label">平均涨跌幅</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">📊 放量历史记录</h2>
                <div class="filter-tabs">
                    <button class="filter-tab active" data-filter="all" onclick="setFilter('all')">全部</button>
                    <button class="filter-tab" data-filter="eth" onclick="setFilter('eth')">ETH</button>
                    <button class="filter-tab" data-filter="xau" onclick="setFilter('xau')">XAU</button>
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>交易对</th>
                        <th>放量倍数</th>
                        <th>成交额</th>
                        <th>涨跌方向</th>
                        <th>涨跌幅</th>
                        <th>价格变化</th>
                        <th>K线时间</th>
                    </tr>
                </thead>
                <tbody id="data-body">
                    <tr>
                        <td colspan="8" class="loading">加载中...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let currentFilter = 'all';
        let allData = [];
        
        function formatNumber(num) {
            if (num >= 1_000_000) {
                return (num / 1_000_000).toFixed(2) + 'M';
            } else if (num >= 1_000) {
                return (num / 1_000).toFixed(2) + 'K';
            }
            return num.toFixed(2);
        }
        
        function formatTime(timestamp) {
            const dt = new Date(timestamp);
            return dt.toLocaleString('zh-CN');
        }
        
        function formatKlineTime(timeStr) {
            const parts = timeStr.split('T');
            if (parts.length === 2) {
                return parts[1].substring(0, 5);
            }
            return timeStr;
        }
        
        function setFilter(filter) {
            currentFilter = filter;
            
            document.querySelectorAll('.filter-tab').forEach(tab => {
                tab.classList.remove('active');
                if (tab.dataset.filter === filter) {
                    tab.classList.add('active');
                }
            });
            
            renderTable();
        }
        
        function renderTable() {
            const tbody = document.getElementById('data-body');
            
            let filteredData = allData;
            if (currentFilter === 'eth') {
                filteredData = allData.filter(d => d.symbol.includes('ETH'));
            } else if (currentFilter === 'xau') {
                filteredData = allData.filter(d => d.symbol.includes('XAU'));
            }
            
            if (filteredData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty">暂无数据</td></tr>';
                return;
            }
            
            tbody.innerHTML = filteredData.map(record => {
                const symbolClass = record.symbol.includes('ETH') ? 'symbol-eth' : 'symbol-xau';
                const directionClass = record.price_direction === '涨' ? 'direction-up' : 
                                      record.price_direction === '跌' ? 'direction-down' : 'direction-neutral';
                const volumeClass = record.volume_ratio >= 5 ? 'volume-high' : '';
                
                return `
                    <tr>
                        <td class="timestamp">${formatTime(record.timestamp)}</td>
                        <td><span class="symbol-badge ${symbolClass}">${record.symbol}</span></td>
                        <td class="${volumeClass}">${record.volume_ratio.toFixed(2)}倍</td>
                        <td>${formatNumber(record.volume)} USDT</td>
                        <td class="${directionClass}">${record.price_direction}</td>
                        <td class="${directionClass}">${record.price_change_percent >= 0 ? '+' : ''}${record.price_change_percent.toFixed(2)}%</td>
                        <td>${record.price_change >= 0 ? '+' : ''}${record.price_change.toFixed(2)}</td>
                        <td>${formatKlineTime(record.kline_time)}</td>
                    </tr>
                `;
            }).join('');
        }
        
        function updateStats() {
            document.getElementById('total-count').textContent = allData.length;
            
            const ethCount = allData.filter(d => d.symbol.includes('ETH')).length;
            const xauCount = allData.filter(d => d.symbol.includes('XAU')).length;
            document.getElementById('eth-count').textContent = ethCount;
            document.getElementById('xau-count').textContent = xauCount;
            
            if (allData.length > 0) {
                const avgChange = allData.reduce((sum, d) => sum + d.price_change_percent, 0) / allData.length;
                document.getElementById('avg-change').textContent = (avgChange >= 0 ? '+' : '') + avgChange.toFixed(2) + '%';
            }
        }
        
        async function loadData() {
            try {
                const response = await fetch('/api/market/volume-spikes');
                const data = await response.json();
                
                if (data.data && data.data.length > 0) {
                    allData = data.data;
                    updateStats();
                    renderTable();
                } else {
                    document.getElementById('data-body').innerHTML = '<tr><td colspan="8" class="empty">暂无放量记录（当有3倍以上放量时会自动记录）</td></tr>';
                }
            } catch (error) {
                console.error('加载数据失败:', error);
                document.getElementById('data-body').innerHTML = '<tr><td colspan="8" class="empty">加载失败，请刷新重试</td></tr>';
            }
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            loadData();
        });
    </script>
</body>
</html>'''
    return html

@app.route('/api/market/status')
def market_status():
    """获取市场监控状态"""
    return jsonify({
        "status": "running",
        "service": "永续合约监控系统",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "monitors": list(CONFIG["MARKET_MONITOR"]["LOG_FILES"].keys()),
    })

@app.route('/api/market/data/eth')
def market_data_eth():
    """获取ETH监控数据"""
    cache = DATA_CACHE["eth"]
    now = time.time()
    
    if cache["data"] is None or (now - cache["timestamp"] > CONFIG["MARKET_MONITOR"]["CACHE_TIME"]):
        cache["data"] = parse_latest_data(CONFIG["MARKET_MONITOR"]["LOG_FILES"]["eth"], "ETH-USDT-SWAP")
        cache["timestamp"] = now
    
    return jsonify(cache["data"])

@app.route('/api/market/data/xau')
def market_data_xau():
    """获取XAU监控数据"""
    cache = DATA_CACHE["xau"]
    now = time.time()
    
    if cache["data"] is None or (now - cache["timestamp"] > CONFIG["MARKET_MONITOR"]["CACHE_TIME"]):
        cache["data"] = parse_latest_data(CONFIG["MARKET_MONITOR"]["LOG_FILES"]["xau"], "XAU-USDT-SWAP")
        cache["timestamp"] = now
    
    return jsonify(cache["data"])

@app.route('/api/market/alerts')
def market_alerts():
    """获取警报记录"""
    cache = DATA_CACHE["alerts"]
    now = time.time()
    
    if cache["data"] is None or (now - cache["timestamp"] > CONFIG["MARKET_MONITOR"]["CACHE_TIME"]):
        cache["data"] = get_today_alerts()
        cache["timestamp"] = now
    
    return jsonify({
        "alerts": cache["data"],
        "count": len(cache["data"]),
        "timestamp": datetime.now().isoformat(),
    })

@app.route('/api/market/history/eth')
def market_history_eth():
    """获取ETH历史数据（用于图表）"""
    history = get_history_data(
        CONFIG["MARKET_MONITOR"]["LOG_FILES"]["eth"],
        "ETH-USDT-SWAP",
        limit=24  # 最近24条（约6小时）
    )
    return jsonify({
        "symbol": "ETH-USDT-SWAP",
        "data": history,
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    })

@app.route('/api/market/history/xau')
def market_history_xau():
    """获取XAU历史数据（用于图表）"""
    history = get_history_data(
        CONFIG["MARKET_MONITOR"]["LOG_FILES"]["xau"],
        "XAU-USDT-SWAP",
        limit=24  # 最近24条（约6小时）
    )
    return jsonify({
        "symbol": "XAU-USDT-SWAP",
        "data": history,
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    })

def get_volume_spike_records(symbol_name, limit=100):
    """读取放量记录数据（优先使用SQLite，fallback到文件）"""
    
    if USE_SQLITE:
        try:
            records = db_get_records(limit=limit, symbol=symbol_name)
            return records
        except Exception as e:
            print(f"SQLite查询失败，回退到文件: {e}")
    
    # Fallback: 从文件读取
    log_file = VOLUME_SPIKE_FILES.get(symbol_name.split('-')[0].lower(), "")
    records = []
    
    if not os.path.exists(log_file):
        return records
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                if record.get('symbol') == symbol_name:
                    records.append(record)
            except json.JSONDecodeError:
                continue
        
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return records[:limit]
        
    except Exception as e:
        print(f"读取放量记录失败: {e}")
        return records

@app.route('/api/market/volume-spikes/eth')
def volume_spikes_eth():
    """获取ETH放量记录"""
    records = get_volume_spike_records("ETH-USDT-SWAP", limit=100)
    return jsonify({
        "symbol": "ETH-USDT-SWAP",
        "data": records,
        "count": len(records),
        "timestamp": datetime.now().isoformat(),
    })

@app.route('/api/market/volume-spikes/xau')
def volume_spikes_xau():
    """获取XAU放量记录"""
    records = get_volume_spike_records("XAU-USDT-SWAP", limit=100)
    return jsonify({
        "symbol": "XAU-USDT-SWAP",
        "data": records,
        "count": len(records),
        "timestamp": datetime.now().isoformat(),
    })

@app.route('/api/market/volume-spikes')
def volume_spikes_all():
    """获取所有放量记录"""
    eth_records = get_volume_spike_records("ETH-USDT-SWAP", limit=100)
    xau_records = get_volume_spike_records("XAU-USDT-SWAP", limit=100)
    
    # 合并并按时间排序
    all_records = eth_records + xau_records
    all_records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jsonify({
        "data": all_records,
        "count": len(all_records),
        "timestamp": datetime.now().isoformat(),
    })

@app.route('/api/market/volume-spikes/stats')
def volume_spikes_stats():
    """获取放量记录统计"""
    if USE_SQLITE:
        try:
            stats = db_get_statistics()
            return jsonify({
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            print(f"统计查询失败: {e}")
    
    return jsonify({
        "stats": {"error": "SQLite不可用"},
        "timestamp": datetime.now().isoformat(),
    })

# ==================== 其他功能路由 ====================
@app.route('/charts_fixed')
@app.route('/charts_fixed/')
def charts_fixed_index():
    """K线图表页面"""
    charts_dir = CONFIG["STATIC_PATHS"]["charts_fixed"]
    # 尝试加载index.html，如果不存在则加载第一个HTML文件
    index_path = os.path.join(charts_dir, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(charts_dir, "index.html")
    else:
        # 查找第一个HTML文件
        html_files = [f for f in os.listdir(charts_dir) if f.endswith('.html')]
        if html_files:
            return send_from_directory(charts_dir, html_files[0])
        else:
            return "No HTML files found in charts_fixed directory", 404

@app.route('/charts_fixed/<path:filename>')
def charts_fixed_static(filename):
    """K线图表静态文件"""
    return send_from_directory(CONFIG["STATIC_PATHS"]["charts_fixed"], filename)

@app.route('/ai-params-viewer')
@app.route('/ai-params-viewer/')
def ai_params_viewer_index():
    """AI参数查看器页面"""
    ai_dir = CONFIG["STATIC_PATHS"]["ai_params_viewer"]
    return send_from_directory(ai_dir, "index.html")

@app.route('/ai-params-viewer/<path:filename>')
def ai_params_viewer_static(filename):
    """AI参数查看器静态文件"""
    return send_from_directory(CONFIG["STATIC_PATHS"]["ai_params_viewer"], filename)

# 添加对根目录.md文件的支持（为了兼容旧的路径）
@app.route('/USER.md')
@app.route('/SOUL.md')
@app.route('/AGENTS.md')
@app.route('/IDENTITY.md')
@app.route('/TOOLS.md')
@app.route('/HEARTBEAT.md')
def serve_root_md_files():
    """提供根目录的Markdown文件（为了兼容性）"""
    import os
    filename = request.path[1:]  # 去掉开头的斜杠
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    else:
        return "File not found", 404

# 添加记忆文件目录列表API
@app.route('/ai-params-viewer/memory/')
def list_memory_files():
    """返回记忆文件列表（简单的HTML目录列表）"""
    import os
    memory_dir = os.path.join(CONFIG["STATIC_PATHS"]["ai_params_viewer"], "memory")
    
    if not os.path.exists(memory_dir):
        return "Memory directory not found", 404
    
    # 获取所有.md文件
    files = [f for f in os.listdir(memory_dir) if f.endswith('.md') and os.path.isfile(os.path.join(memory_dir, f))]
    files.sort(reverse=True)  # 按日期倒序
    
    # 生成简单的HTML目录列表（兼容Apache风格）
    html = "<!DOCTYPE html>\n<html>\n<head><title>Memory Files</title></head>\n<body>\n<h1>Memory Files</h1>\n<ul>\n"
    for f in files:
        html += f'<li><a href="{f}">{f}</a></li>\n'
    html += "</ul>\n</body>\n</html>"
    
    return html

# ==================== 主程序 ====================
if __name__ == '__main__':
    print("🚀 启动统一多功能应用...")
    print(f"🌐 统一入口: http://localhost:{CONFIG['PORT']}")
    print(f"📊 市场监控: http://localhost:{CONFIG['PORT']}/market_monitor")
    print(f"📈 K线图表: http://localhost:{CONFIG['PORT']}/charts_fixed")
    print(f"🤖 AI参数: http://localhost:{CONFIG['PORT']}/ai-params-viewer")
    print("="*60)
    
    # 检查日志文件
    print("🔍 检查市场监控日志文件:")
    for symbol, log_file in CONFIG["MARKET_MONITOR"]["LOG_FILES"].items():
        if os.path.exists(log_file):
            print(f"  ✅ {symbol.upper()}: 存在")
        else:
            print(f"  ⚠️ {symbol.upper()}: 不存在")
    
    # 检查静态文件目录
    print("🔍 检查静态文件目录:")
    for name, path in CONFIG["STATIC_PATHS"].items():
        if os.path.exists(path):
            files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
            print(f"  ✅ {name}: 存在 ({files}个文件)")
        else:
            print(f"  ⚠️ {name}: 不存在")

# ==================== 抖音EMO系统页面 ====================
@app.route('/douyin_emo')
def douyin_emo_index():
    """抖音EMO系统主页面"""
    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>抖音共鸣系统 | 小龙虾平台</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                min-height: 100vh;
                padding: 30px;
                color: #333;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            }
            
            .header {
                text-align: center;
                margin-bottom: 50px;
                padding-bottom: 30px;
                border-bottom: 3px solid #f5576c;
            }
            
            .header h1 {
                font-size: 2.5rem;
                color: #2d3748;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }
            
            .header .subtitle {
                color: #4a5568;
                font-size: 1.1rem;
                opacity: 0.9;
                max-width: 700px;
                margin: 0 auto;
                line-height: 1.6;
            }
            
            .back-link {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                color: #f5576c;
                text-decoration: none;
                font-weight: 600;
                margin-bottom: 30px;
                transition: all 0.3s;
            }
            
            .back-link:hover {
                color: #e9455c;
                transform: translateX(-5px);
            }
            
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 30px;
                margin-top: 30px;
            }
            
            .feature-card {
                background: white;
                border-radius: 15px;
                padding: 35px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
                text-decoration: none;
                color: inherit;
                border: 2px solid transparent;
            }
            
            .feature-card:hover {
                transform: translateY(-8px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                border-color: #f5576c;
            }
            
            .feature-card h2 {
                font-size: 1.5rem;
                color: #2d3748;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .feature-card .emoji {
                font-size: 2rem;
            }
            
            .feature-card p {
                color: #4a5568;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            
            .feature-card .features {
                list-style: none;
            }
            
            .feature-card .features li {
                padding: 6px 0;
                color: #718096;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .feature-card .features li:before {
                content: "✨";
                font-size: 0.8rem;
            }
            
            .status-badge {
                display: inline-block;
                padding: 6px 14px;
                background: linear-gradient(135deg, #f093fb, #f5576c);
                color: white;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-top: 15px;
            }
            
            .info-section {
                background: #f7fafc;
                border-radius: 12px;
                padding: 25px;
                margin-top: 40px;
            }
            
            .info-section h3 {
                color: #2d3748;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }
            
            .info-section p {
                color: #718096;
                line-height: 1.7;
            }
            
            .footer {
                text-align: center;
                margin-top: 50px;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
                color: #718096;
                font-size: 0.9rem;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                .header h1 {
                    font-size: 2rem;
                    flex-direction: column;
                }
                
                .feature-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">
                <span>←</span> 返回首页
            </a>
            
            <div class="header">
                <h1>
                    <span class="emoji">🎬</span>
                    抖音共鸣系统
                </h1>
                <p class="subtitle">
                    为抖音EMO视频号打造的智能内容生成系统<br>
                    自动生成15秒情感共鸣视频，精准触达18-25岁EMO女生群体
                </p>
            </div>
            
            <div class="feature-grid">
                <a href="/emo_hooks_preview.html" class="feature-card">
                    <h2>
                        <span class="emoji">📝</span>
                        查看文案库
                    </h2>
                    <p>
                        100条精选情感钩子文案，涵盖4种核心类型，支持预览和搜索。
                    </p>
                    <ul class="features">
                        <li>4种钩子类型</li>
                        <li>100条精选文案</li>
                        <li>支持关键词搜索</li>
                        <li>一键复制文案</li>
                    </ul>
                    <div class="status-badge">点击进入 →</div>
                </a>
                
                <a href="/douyin_emo/videos" class="feature-card">
                    <h2>
                        <span class="emoji">🎥</span>
                        查看视频效果
                    </h2>
                    <p>
                        已生成的视频列表，可在线预览播放，直观查看生成效果。
                    </p>
                    <ul class="features">
                        <li>视频在线播放</li>
                        <li>文案描述对应</li>
                        <li>批量预览</li>
                        <li>下载功能</li>
                    </ul>
                    <div class="status-badge">点击进入 →</div>
                </a>
            </div>
            
            <div class="info-section">
                <h3>📌 系统说明</h3>
                <p>
                    抖音共鸣系统专为抖音EMO视频号设计，通过4种情感钩子类型（替我说、与我同频、扎心真相、留白召唤），
                    精准触达目标用户。每条视频15秒，包含完整的Hook→展开→峰值→留白结构，配合AI语音和字幕生成，
                    实现批量内容生产。
                </p>
            </div>
            
            <div class="footer">
                <p>🎬 抖音共鸣系统 | 专为EMO视频号打造</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# ==================== 抖音EMO视频列表 ====================
@app.route('/douyin_emo/videos')
def douyin_emo_videos():
    """抖音EMO视频列表页面"""
    import glob
    
    videos_dir = '/root/.openclaw/workspace/douyin_emo/output/videos'
    videos = []
    
    # 获取所有 mp4 文件
    for f in sorted(glob.glob(f'{videos_dir}/*.mp4')):
        filename = os.path.basename(f)
        if filename.startswith('0') or filename.startswith('video'):
            # 获取文件大小
            size = os.path.getsize(f)
            size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
            
            # 尝试从 tracking_table 获取文案描述
            description = filename
            tracking_file = '/root/.openclaw/workspace/douyin_emo/tracking_table.md'
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r', encoding='utf-8') as tf:
                    for line in tf:
                        if filename.replace('.mp4', '.mp3') in line or f"| {filename.replace('.mp4', '')} |" in line:
                            # 提取文案内容
                            parts = line.split('|')
                            if len(parts) > 2:
                                description = parts[2].strip()[:50] + '...' if len(parts[2].strip()) > 50 else parts[2].strip()
                            break
            
            videos.append({
                'filename': filename,
                'url': f'/douyin_emo/videos/{filename}',
                'size': size_str,
                'description': description
            })
    
    videos_html = ''
    for v in videos:
        videos_html += f'''
        <div class="video-card">
            <video controls preload="metadata">
                <source src="{v['url']}" type="video/mp4">
                您的浏览器不支持视频播放
            </video>
            <div class="video-info">
                <h4>{v['filename']}</h4>
                <p class="description">{v['description']}</p>
                <p class="size">📁 {v['size']}</p>
                <a href="{v['url']}" target="_blank" class="download-link">新窗口打开 →</a>
            </div>
        </div>
        '''
    
    if not videos:
        videos_html = '<p class="no-videos">暂无可用视频，请先生成视频文件</p>'
    
    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>抖音EMO视频列表 | 小龙虾平台</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }}
            
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 30px;
                color: #333;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 25px;
                border-bottom: 3px solid #e2e8f0;
            }}
            
            .header h1 {{
                font-size: 2rem;
                color: #2d3748;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }}
            
            .back-link {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                margin-bottom: 20px;
                transition: all 0.3s;
            }}
            
            .back-link:hover {{
                color: #5a67d8;
                transform: translateX(-5px);
            }}
            
            .videos-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
            }}
            
            .video-card {{
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }}
            
            .video-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
            }}
            
            .video-card video {{
                width: 100%;
                aspect-ratio: 9/16;
                object-fit: cover;
                background: #000;
            }}
            
            .video-info {{
                padding: 20px;
            }}
            
            .video-info h4 {{
                color: #2d3748;
                font-size: 1.1rem;
                margin-bottom: 8px;
            }}
            
            .video-info .description {{
                color: #718096;
                font-size: 0.9rem;
                margin-bottom: 8px;
                line-height: 1.5;
            }}
            
            .video-info .size {{
                color: #a0aec0;
                font-size: 0.85rem;
                margin-bottom: 10px;
            }}
            
            .download-link {{
                display: inline-block;
                padding: 6px 12px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border-radius: 8px;
                text-decoration: none;
                font-size: 0.85rem;
                transition: all 0.3s;
            }}
            
            .download-link:hover {{
                transform: scale(1.05);
            }}
            
            .no-videos {{
                text-align: center;
                color: #718096;
                padding: 60px 20px;
                font-size: 1.1rem;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 25px;
                border-top: 2px solid #e2e8f0;
                color: #718096;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/douyin_emo" class="back-link">
                <span>←</span> 返回抖音EMO系统
            </a>
            
            <div class="header">
                <h1>
                    <span class="emoji">🎥</span>
                    抖音EMO视频列表
                </h1>
            </div>
            
            <div class="videos-grid">
                {videos_html}
            </div>
            
            <div class="footer">
                <p>🎬 抖音共鸣系统 | 视频列表</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# ==================== 抖音EMO视频静态文件 ====================
@app.route('/douyin_emo/videos/<path:filename>')
def douyin_emo_video_static(filename):
    """抖音EMO视频静态文件"""
    video_path = f'/root/.openclaw/workspace/douyin_emo/output/videos/{filename}'
    if os.path.exists(video_path):
        return send_file(video_path)
    return "视频文件不存在", 404

# ==================== 抖音EMO钩子预览 ====================
@app.route('/emo_hooks_preview')
@app.route('/emo_hooks_preview.html')
def emo_hooks_preview():
    """抖音EMO钩子预览页面"""
    html_path = '/root/.openclaw/workspace/douyin_emo/output/emo_hooks_preview.html'
    if os.path.exists(html_path):
        return send_file(html_path)
    return "emo_hooks_preview.html 文件不存在", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=CONFIG['PORT'], debug=CONFIG['DEBUG'])
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CONFIG["PORT"], debug=CONFIG["DEBUG"])
