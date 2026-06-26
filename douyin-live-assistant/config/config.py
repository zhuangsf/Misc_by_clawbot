# 配置文件
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 服务配置
HOST = "0.0.0.0"
PORT = 8888

# 浏览器配置
BROWSER_CONFIG = {
    "headless": False,  # 显示浏览器窗口
    "viewport": {"width": 1280, "height": 720},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# 行为随机化配置
ANTI_DETECTION = {
    "min_like_interval": 3,    # 最小点赞间隔（秒）
    "max_like_interval": 10,   # 最大点赞间隔（秒）
    "max_runtime_hours": 3,    # 单账号最大运行时长
    "refresh_interval": 1800,  # 刷新页面间隔（秒）
}

# 数据库
DATABASE_PATH = os.path.join(BASE_DIR, "data", "douyin.db")

# Cookies存储目录
COOKIES_DIR = os.path.join(BASE_DIR, "cookies")

# 日志
LOG_DIR = os.path.join(BASE_DIR, "logs")
