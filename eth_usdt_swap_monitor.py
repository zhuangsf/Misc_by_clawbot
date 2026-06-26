#!/usr/bin/env python3
"""
ETH-USDT-SWAP 永续合约15分钟K线成交量监控程序
监控OKX ETH永续合约成交量，检测3倍放大异动
"""

import os
import sys
import time
import json
import schedule
import traceback
import subprocess
from datetime import datetime, timedelta

# 添加到系统路径，确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入SQLite模块（用于放量记录持久化）
try:
    from volume_spikes_db import add_record as db_add_record, init_db as db_init
    USE_DB = True
    db_init()  # 确保数据库已初始化
    print("✅ 放量记录SQLite模块已加载")
except ImportError as e:
    USE_DB = False
    print(f"⚠️ 无法导入SQLite模块: {e}")

from okx import MarketData

# ==================== 配置区域 ====================
CONFIG = {
    # 监控配置 - ETH永续合约
    "SYMBOL": "ETH-USDT-SWAP",
    "KLINE_INTERVAL": "15m",      # 15分钟K线
    "CHECK_INTERVAL": 5,          # 每5分钟检查一次
    "VOLUME_MULTIPLIER": 3,       # 3倍成交量触发
    
    # API配置
    "API_KEY": "a8a1594d-a0ac-4832-9541-a1ad3c63ab47",
    "SECRET_KEY": "EEE3E62D86CD55098DAC449C8E05908F",
    "PROXY": "http://127.0.0.1:7890",
    
    # 飞书接收者
    "FEISHU_USER_ID": "ou_cfad6c31585c95cc96b47b7698b0628c",
    
    # 日志配置
    "LOG_FILE": "/root/.openclaw/workspace/eth_swap_monitor.log",
    "VOLUME_LOG_FILE": "/root/.openclaw/workspace/volume_spike_records.log",  # 放量记录文件
    "MAX_LOG_SIZE": 10 * 1024 * 1024,  # 10MB
}

# 全局状态
STATE = {
    "last_alert_time": None,
    "last_alert_kline_time": None,
    "start_time": datetime.now(),
    "check_count": 0,
    "alert_count": 0,
    "current_date": datetime.now().strftime("%Y-%m-%d"),  # 用于每日重置统计
}

# ==================== 日志功能 ====================
def setup_logging():
    """设置日志"""
    import logging
    
    logger = logging.getLogger('eth_swap_monitor')
    logger.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if CONFIG["LOG_FILE"]:
        try:
            file_handler = logging.FileHandler(CONFIG["LOG_FILE"], encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"无法创建日志文件: {e}")
    
    return logger

logger = setup_logging()

# ==================== OKX API客户端 ====================
def create_okx_client():
    """创建OKX API客户端"""
    try:
        client = MarketData.MarketAPI(
            api_key=CONFIG["API_KEY"],
            api_secret_key=CONFIG["SECRET_KEY"],
            passphrase="",
            flag="0",
            debug=False,
            proxy=CONFIG["PROXY"]
        )
        logger.info(f"✅ OKX客户端创建成功 (用于{CONFIG['SYMBOL']}永续合约)")
        return client
    except Exception as e:
        logger.error(f"❌ 创建OKX客户端失败: {e}")
        return None

okx_client = create_okx_client()

# ==================== 格式化函数 ====================
def format_volume_usdt(volume_usdt):
    """格式化成交额显示（K/M格式）"""
    if volume_usdt >= 1_000_000:  # 1M以上
        return f"{volume_usdt / 1_000_000:.2f}M"
    elif volume_usdt >= 1_000:  # 1K以上
        return f"{volume_usdt / 1_000:.2f}K"
    else:
        return f"{volume_usdt:.2f}"

# ==================== 核心监控功能 ====================
def get_kline_data():
    """获取最新的15分钟K线数据"""
    if not okx_client:
        logger.error("OKX客户端未初始化")
        return None
    
    try:
        result = okx_client.get_candlesticks(
            instId=CONFIG["SYMBOL"],
            bar=CONFIG["KLINE_INTERVAL"],
            limit="2"  # 只获取最新的2根K线
        )
        
        if result['code'] == '0' and result['data']:
            return result['data']
        else:
            logger.error(f"获取K线数据失败: {result.get('msg', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"获取K线数据异常: {e}")
        traceback.print_exc()
        return None

def parse_kline_data(kline_data):
    """解析K线数据"""
    if not kline_data or len(kline_data) < 2:
        return None
    
    try:
        # kline_data[0]是当前K线，kline_data[1]是前一K线
        current_kline = kline_data[0]
        previous_kline = kline_data[1]
        
        current_timestamp = datetime.fromtimestamp(int(current_kline[0]) / 1000)
        previous_timestamp = datetime.fromtimestamp(int(previous_kline[0]) / 1000)
        
        data = {
            'current': {
                'timestamp': current_timestamp,
                'volume': float(current_kline[5]),  # 币种成交量（ETH）
                'volume_usdt': float(current_kline[7]) if len(current_kline) > 7 else 0,  # USD成交额
                'open': float(current_kline[1]),
                'high': float(current_kline[2]),
                'low': float(current_kline[3]),
                'close': float(current_kline[4]),
                'is_completed': current_kline[8] == '1'
            },
            'previous': {
                'timestamp': previous_timestamp,
                'volume': float(previous_kline[5]),  # 币种成交量（ETH）
                'volume_usdt': float(previous_kline[7]) if len(previous_kline) > 7 else 0,  # USD成交额
                'open': float(previous_kline[1]),
                'high': float(previous_kline[2]),
                'low': float(previous_kline[3]),
                'close': float(previous_kline[4]),
                'is_completed': previous_kline[8] == '1'
            }
        }
        
        return data
        
    except Exception as e:
        logger.error(f"解析K线数据异常: {e}")
        return None

def send_feishu_alert(message):
    """发送警报到飞书"""
    try:
        clean_message = message.strip()
        
        cmd = (
            f"openclaw message send --channel feishu "
            f"--target user:{CONFIG['FEISHU_USER_ID']} "
            f'--message "{clean_message}"'
        )
        
        logger.info("正在发送ETH永续合约警报到飞书...")
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("✅ ETH永续合约警报已成功发送到飞书")
            STATE['alert_count'] += 1
            return True
        else:
            logger.error(f"❌ 发送ETH永续合约警报失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("发送消息超时")
        return False
    except Exception as e:
        logger.error(f"发送警报异常: {e}")
        traceback.print_exc()
        return False

def check_volume_spike():
    """检查成交量异动"""
    # 检查是否新的一天，重置每日统计
    today = datetime.now().strftime("%Y-%m-%d")
    if today != STATE["current_date"]:
        logger.info(f"🌅 新的一天开始了！重置统计数据（{STATE['current_date']} -> {today}）")
        STATE["current_date"] = today
        STATE["check_count"] = 0
        STATE["alert_count"] = 0
        STATE["start_time"] = datetime.now()  # 重置运行时间
    
    STATE['check_count'] += 1
    
    logger.info(f"开始第{STATE['check_count']}次检查...")
    
    # 获取K线数据
    kline_data = get_kline_data()
    if not kline_data:
        logger.warning("获取K线数据失败，跳过本次检查")
        return
    
    # 解析数据
    parsed_data = parse_kline_data(kline_data)
    if not parsed_data:
        logger.warning("解析K线数据失败，跳过本次检查")
        return
    
    current = parsed_data['current']
    previous = parsed_data['previous']
    
    logger.info(f"当前K线: {current['timestamp']}, 成交额: {format_volume_usdt(current['volume_usdt'])} USDT ({'进行中' if not current['is_completed'] else '已完成'})")
    logger.info(f"前一K线: {previous['timestamp']}, 成交额: {format_volume_usdt(previous['volume_usdt'])} USDT ({'进行中' if not previous['is_completed'] else '已完成'})")
    
    # 记录已完成的K线数据（供历史图表使用）
    if previous['is_completed']:
        prev_ratio = previous['volume_usdt'] / current['volume_usdt'] if current['volume_usdt'] > 0 else 0
        logger.info(f"✅ K线完成记录 | 时间: {previous['timestamp']} | 成交额: {format_volume_usdt(previous['volume_usdt'])} USDT | 与当前比: {prev_ratio:.2f}倍")
    
    # 输出价格变化信息
    current_close = current['close']
    previous_close = previous['close']
    price_change = current_close - previous_close
    price_change_percent = (price_change / previous_close * 100) if previous_close > 0 else 0
    price_direction = "涨" if price_change > 0 else ("跌" if price_change < 0 else "平")
    logger.info(f"价格变化: {previous_close:.2f} → {current_close:.2f} USDT ({price_change:+.2f}, {price_change_percent:+.2f}%, {price_direction})")
    
    # 计算成交额倍数
    if previous['volume_usdt'] > 0:
        volume_ratio = current['volume_usdt'] / previous['volume_usdt']
        logger.info(f"成交额倍数: {volume_ratio:.2f}倍")
        
        # 检查是否触发警报
        if volume_ratio >= CONFIG['VOLUME_MULTIPLIER']:
            # 检查是否重复警报（同一根K线只报警一次）
            if STATE['last_alert_kline_time'] == current['timestamp']:
                logger.info("同一K线已报警过，跳过重复警报")
                return
            
            # 准备警报消息
            price_change = current['close'] - current['open']
            price_change_percent = (price_change / current['open'] * 100) if current['open'] > 0 else 0
            
            alert_message = f"""🚨 **ETH-USDT-SWAP 15分钟K线成交额异常！** ⚡️

📊 **K线信息:**
- 当前K线: {current['timestamp']} ({'已完成' if current['is_completed'] else '进行中'})
- 前一K线: {previous['timestamp']}

📈 **成交额数据:**
- 当前成交额: {format_volume_usdt(current['volume_usdt'])} USDT
- 前一成交额: {format_volume_usdt(previous['volume_usdt'])} USDT  
- 成交额倍数: **{volume_ratio:.2f}倍**

💰 **价格信息:**
- 开盘价: {current['open']:.2f} USDT
- 收盘价: {current['close']:.2f} USDT
- 价格变化: {price_change:+.2f} USDT ({price_change_percent:+.2f}%)

⏰ **检测时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚡️ **触发条件:** 当前15分钟K线成交额 > 前一K线成交额 × {CONFIG['VOLUME_MULTIPLIER']}

🏷️ **合约类型:** OKX ETH永续合约"""
            
            # 发送警报
            if send_feishu_alert(alert_message):
                STATE['last_alert_time'] = datetime.now()
                STATE['last_alert_kline_time'] = current['timestamp']
                
                # 记录放量数据到单独文件
                record_volume_spike(current, previous, volume_ratio)
        else:
            logger.info(f"成交额正常 ({volume_ratio:.2f}倍 < {CONFIG['VOLUME_MULTIPLIER']}倍)")
    else:
        logger.warning("前一K线成交额为0，无法计算倍数")
    
    # 每次检查后输出运行时间（供前端解析）
    uptime = datetime.now() - STATE['start_time']
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    logger.info(f"📊 状态 | 运行时间: {uptime.days}天 {hours}时 {minutes}分 {seconds}秒 | 检查次数: {STATE['check_count']} | 警报次数: {STATE['alert_count']}")

def record_volume_spike(current, previous, volume_ratio):
    """记录放量数据到数据库和日志文件"""
    try:
        # 计算价格变化
        price_change = current['close'] - current['open']
        price_change_percent = (price_change / current['open'] * 100) if current['open'] > 0 else 0
        price_direction = "涨" if price_change > 0 else ("跌" if price_change < 0 else "平")
        
        # 准备记录数据（包含完整K线数据用于回测）
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": CONFIG["SYMBOL"],
            "kline_time": current['timestamp'].isoformat() if hasattr(current['timestamp'], 'isoformat') else str(current['timestamp']),
            "volume": current['volume_usdt'],
            "volume_ratio": volume_ratio,
            "price_direction": price_direction,
            "price_change_percent": price_change_percent,
            "price_change": price_change,
            "previous_volume": previous['volume_usdt'],
            # 完整K线数据（用于回测）
            "kline_open": current['open'],
            "kline_high": current.get('high', current['close']),
            "kline_low": current.get('low', current['close']),
            "kline_close": current['close'],
            "kline_timestamp": str(current.get('timestamp', '')),
        }
        
        # 1. 写入SQLite数据库（主存储）
        if USE_DB:
            try:
                db_add_record(record)
            except Exception as e:
                logger.error(f"写入SQLite失败: {e}")
        
        # 2. 写入JSON日志文件（备份/兼容）
        try:
            with open(CONFIG['VOLUME_LOG_FILE'], 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"写入日志文件失败: {e}")
        
        logger.info(f"✅ 放量记录已保存: {record['kline_time']} | {volume_ratio:.2f}倍 | 价格变化: {price_change_percent:+.2f}%")
        
    except Exception as e:
        logger.error(f"记录放量数据失败: {e}")
        traceback.print_exc()

def print_status():
    """打印监控状态"""
    uptime = datetime.now() - STATE['start_time']
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    status_message = f"""
📊 ETH-USDT-SWAP永续合约监控状态
{'='*50}
🏃 运行时间: {uptime.days}天 {hours}时 {minutes}分 {seconds}秒
🔍 检查次数: {STATE['check_count']}
🚨 警报次数: {STATE['alert_count']}
📈 监控配置:
   - 交易对: {CONFIG['SYMBOL']}
   - 合约类型: OKX永续合约
   - K线周期: {CONFIG['KLINE_INTERVAL']}
   - 检查频率: 每{CONFIG['CHECK_INTERVAL']}分钟
   - 触发条件: {CONFIG['VOLUME_MULTIPLIER']}倍成交额
🕐 下次检查: {datetime.now() + timedelta(minutes=CONFIG['CHECK_INTERVAL'])}
{'='*50}
"""
    logger.info(status_message)

# ==================== 主程序 ====================
def run_monitor():
    """运行监控程序"""
    logger.info("🚀 ETH-USDT-SWAP永续合约成交额监控程序启动！")
    logger.info("🎯 监控目标: OKX ETH永续合约 (ETHUSDT永续合约)")
    logger.info(f"📊 配置: {CONFIG['SYMBOL']}, {CONFIG['KLINE_INTERVAL']}K线, 每{CONFIG['CHECK_INTERVAL']}分钟检查")
    
    # 初始状态报告
    print_status()
    
    # 立即执行一次检查
    check_volume_spike()
    
    # 设置定时任务
    schedule.every(CONFIG['CHECK_INTERVAL']).minutes.do(check_volume_spike)
    
    # 每30分钟打印一次状态
    schedule.every(30).minutes.do(print_status)
    
    logger.info(f"定时任务已设置: 每{CONFIG['CHECK_INTERVAL']}分钟检查一次")
    
    # 保持程序运行
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("监控程序被用户中断")
        print_status()
    except Exception as e:
        logger.error(f"监控程序异常: {e}")
        traceback.print_exc()
        sys.exit(1)

def main():
    """主函数"""
    # 设置代理
    if CONFIG["PROXY"]:
        os.environ['HTTP_PROXY'] = CONFIG["PROXY"]
        os.environ['HTTPS_PROXY'] = CONFIG["PROXY"]
    
    # 检查必要配置
    if not CONFIG["FEISHU_USER_ID"]:
        logger.error("未配置飞书用户ID")
        sys.exit(1)
    
    # 运行监控
    run_monitor()

if __name__ == "__main__":
    main()