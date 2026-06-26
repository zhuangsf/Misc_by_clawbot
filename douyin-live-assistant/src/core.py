# 抖音直播挂机助手 - 核心模块

import os
import json
import time
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from config.config import DATABASE_PATH, COOKIES_DIR, LOG_DIR, BROWSER_CONFIG, ANTI_DETECTION

# 确保目录存在
os.makedirs(COOKIES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== 数据库模块 ====================

def init_db():
    """初始化数据库"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # 账号表
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name TEXT NOT NULL,
        cookies_file TEXT,
        proxy_url TEXT,
        status TEXT DEFAULT 'offline',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 任务表
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id TEXT NOT NULL,
        account_ids TEXT,
        status TEXT DEFAULT 'stopped',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 日志表
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        action TEXT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

# ==================== 账号管理模块 ====================

def add_account(account_name: str) -> int:
    """添加账号"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO accounts (account_name, status) VALUES (?, ?)", (account_name, "offline"))
    account_id = c.lastrowid
    conn.commit()
    conn.close()
    return account_id

def get_accounts():
    """获取所有账号"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()
    conn.close()
    return accounts

def update_account_status(account_id: int, status: str):
    """更新账号状态"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
    conn.commit()
    conn.close()

def delete_account(account_id: int):
    """删除账号"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT cookies_file FROM accounts WHERE id = ?", (account_id,))
    result = c.fetchone()
    if result and result[0] and os.path.exists(result[0]):
        os.remove(result[0])
    c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()

# ==================== 任务管理模块 ====================

def create_task(room_id: str, account_ids: list) -> int:
    """创建任务"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (room_id, account_ids, status) VALUES (?, ?, ?)", 
              (room_id, json.dumps(account_ids), "stopped"))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks():
    """获取所有任务"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str):
    """更新任务状态"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

# ==================== 浏览器管理 ====================

class BrowserPool:
    """浏览器池管理"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts = {}  # account_id -> context
    
    def start(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            print("✅ 浏览器已启动")
    
    def create_context(self, account_id: int, proxy_url: str = None):
        """为账号创建独立的浏览器上下文"""
        context_options = {
            "viewport": BROWSER_CONFIG["viewport"],
            "user_agent": BROWSER_CONFIG["user_agent"],
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
        }
        
        # 如果有代理，配置代理
        if proxy_url:
            context_options["proxy"] = {"server": proxy_url}
        
        context = self.browser.new_context(**context_options)
        self.contexts[account_id] = context
        return context
    
    def get_context(self, account_id: int):
        return self.contexts.get(account_id)
    
    def close_context(self, account_id: int):
        if account_id in self.contexts:
            self.contexts[account_id].close()
            del self.contexts[account_id]
    
    def stop(self):
        for ctx in self.contexts.values():
            ctx.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ 浏览器已关闭")

# 全局浏览器池
browser_pool = BrowserPool()

# ==================== 登录模块 ====================

def save_cookies(context: BrowserContext, account_id: int):
    """保存cookies"""
    cookies = context.cookies()
    cookies_file = os.path.join(COOKIES_DIR, f"account_{account_id}.json")
    with open(cookies_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    
    # 更新数据库
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE accounts SET cookies_file = ? WHERE id = ?", (cookies_file, account_id))
    conn.commit()
    conn.close()
    return cookies_file

def load_cookies(account_id: int) -> list:
    """加载cookies"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT cookies_file FROM accounts WHERE id = ?", (account_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] and os.path.exists(result[0]):
        with open(result[0], "r", encoding="utf-8") as f:
            return json.load(f)
    return []

async def login_douyin(context: BrowserContext) -> Page:
    """登录抖音（扫码登录）"""
    page = context.new_page()
    
    # 访问抖音登录页
    page.goto("https://www.douyin.com/")
    page.wait_for_load_state("networkidle")
    
    # 检查是否已登录
    if is_logged_in(page):
        print("✅ 已登录")
        return page
    
    # 点击登录按钮
    page.click('text="登录"')
    page.wait_for_timeout(1000)
    
    # 选择扫码登录
    page.click('text="扫码登录"')
    page.wait_for_timeout(1000)
    
    # 等待二维码出现
    qrcode_selector = ".qrcode-img img, .qrcode img"
    page.wait_for_selector(qrcode_selector, timeout=10000)
    
    print("📱 请扫码登录抖音...")
    
    # 等待登录成功（轮询检查）
    while not is_logged_in(page):
        page.wait_for_timeout(2000)
        if page.is_visible('text="登录"'):
            print("⏳ 等待扫码中...")
    
    print("✅ 登录成功!")
    return page

def is_logged_in(page: Page) -> bool:
    """检查是否已登录"""
    # 检查是否有登录按钮（未登录状态）
    try:
        # 尝试点击头像或用户名区域（已登录状态）
        page.wait_for_selector('.header-avatar, .user-avatar, [class*="avatar"]', timeout=3000)
        return True
    except:
        return False

# ==================== 直播间执行器 ====================

class LiveRoomRunner:
    """直播间挂机执行器"""
    
    def __init__(self, account_id: int, room_id: str):
        self.account_id = account_id
        self.room_id = room_id
        self.context = None
        self.page = None
        self.running = False
        self.start_time = None
    
    def start(self):
        """启动挂机"""
        self.running = True
        self.start_time = time.time()
        update_account_status(self.account_id, "online")
        
        # 获取或创建浏览器上下文
        self.context = browser_pool.get_context(self.account_id)
        if not self.context:
            self.context = browser_pool.create_context(self.account_id)
        
        # 加载cookies
        cookies = load_cookies(self.account_id)
        if cookies:
            self.context.add_cookies(cookies)
        
        # 访问直播间
        self.page = self.context.new_page()
        self.page.goto(f"https://live.douyin.com/{self.room_id}")
        self.page.wait_for_load_state("networkidle")
        
        # 等待进入直播间
        self.page.wait_for_timeout(3000)
        
        print(f"🎬 账号 {self.account_id} 已进入直播间: {self.room_id}")
        
        # 开始循环点赞
        self._run_like_loop()
    
    def _run_like_loop(self):
        """点赞循环"""
        while self.running:
            # 检查运行时长
            if self.start_time and (time.time() - self.start_time) > ANTI_DETECTION["max_runtime_hours"] * 3600:
                print(f"⏰ 账号 {self.account_id} 运行时间已达上限，停止")
                break
            
            try:
                # 随机延迟
                delay = random.uniform(
                    ANTI_DETECTION["min_like_interval"],
                    ANTI_DETECTION["max_like_interval"]
                )
                self.page.wait_for_timeout(delay * 1000)
                
                # 尝试点赞
                self._like()
                
                # 偶尔滑动页面（模拟浏览）
                if random.random() < 0.1:  # 10%概率
                    self._scroll()
                    
            except Exception as e:
                print(f"❌ 账号 {self.account_id} 执行出错: {e}")
                self.page.wait_for_timeout(5000)
        
        self.stop()
    
    def _like(self):
        """点赞"""
        try:
            # 查找点赞按钮并点击
            # 抖音直播间点赞按钮通常在右侧
            like_button = self.page.locator('[class*="like"], .like-btn, [d*="M19"]').first
            if like_button.is_visible():
                like_button.click()
                print(f"👍 账号 {self.account_id} 点赞成功")
        except Exception as e:
            print(f"⚠️ 点赞失败: {e}")
    
    def _scroll(self):
        """滑动页面"""
        try:
            self.page.evaluate("window.scrollBy(0, Math.random() * 200 + 100)")
        except:
            pass
    
    def stop(self):
        """停止挂机"""
        self.running = False
        update_account_status(self.account_id, "offline")
        
        # 保存cookies
        if self.context and self.page:
            save_cookies(self.context, self.account_id)
        
        print(f"🛑 账号 {self.account_id} 已停止")

# ==================== 日志模块 ====================

def add_log(account_id: int, action: str, message: str):
    """添加日志"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO logs (account_id, action, message) VALUES (?, ?, ?)", 
              (account_id, action, message))
    conn.commit()
    conn.close()

def get_logs(limit: int = 100):
    """获取日志"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT ?", (limit,))
    logs = c.fetchall()
    conn.close()
    return logs
