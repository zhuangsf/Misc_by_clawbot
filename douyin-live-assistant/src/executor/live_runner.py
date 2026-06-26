"""
直播间执行器 - 核心挂机逻辑
"""
import asyncio
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Warning: playwright not installed, using placeholder")

from models import get_connection

# 配置
BASE_DIR = Path(__file__).parent.parent
COOKIES_DIR = BASE_DIR / "cookies"
CONFIG = {
    "min_like_interval": 3,
    "max_like_interval": 10,
    "max_runtime_hours": 3,
    "refresh_interval": 1800,
}


class LiveRoomRunner:
    """直播间执行器"""
    
    def __init__(self, account_id, account_name, cookies_file):
        self.account_id = account_id
        self.account_name = account_name
        self.cookies_file = cookies_file
        self.browser = None
        self.page = None
        self.running = False
        self.start_time = None
        
    async def start(self, room_id):
        """启动挂机"""
        self.running = True
        self.start_time = time.time()
        
        async with async_playwright() as p:
            # 启动浏览器（非headless，显示窗口）
            self.browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # 创建上下文（带随机指纹）
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 加载cookies
            await self._load_cookies(context)
            
            # 创建页面
            self.page = await context.new_page()
            
            # 进入直播间
            room_url = f"https://live.douyin.com/{room_id}"
            print(f"[{self.account_name}] 进入直播间: {room_url}")
            await self.page.goto(room_url)
            
            # 等待页面加载
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 更新状态
            self._update_status("online")
            self._log("info", f"进入直播间 {room_id}")
            
            # 开始挂机循环
            await self._run_loop(room_id)
            
            await context.close()
            await self.browser.close()
    
    async def _load_cookies(self, context):
        """加载cookies"""
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print(f"[{self.account_name}] 已加载cookies")
    
    async def _run_loop(self, room_id):
        """主循环"""
        like_count = 0
        
        while self.running:
            # 检查运行时长
            if time.time() - self.start_time > CONFIG["max_runtime_hours"] * 3600:
                print(f"[{self.account_name}] 达到最大运行时长，停止")
                break
            
            try:
                # 随机延迟
                delay = random.randint(CONFIG["min_like_interval"], CONFIG["max_like_interval"])
                await asyncio.sleep(delay)
                
                if not self.running:
                    break
                
                # 尝试点赞
                liked = await self._like()
                if liked:
                    like_count += 1
                    print(f"[{self.account_name}] 点赞成功，累计: {like_count}")
                    self._log("like", f"点赞成功，累计: {like_count}")
                
            except Exception as e:
                print(f"[{self.account_name}] 错误: {e}")
                self._log("error", str(e))
        
        self._update_status("offline")
        self._log("info", f"任务结束，共点赞 {like_count} 次")
    
    async def _like(self):
        """执行点赞"""
        try:
            # 查找点赞按钮 - 抖音直播间点赞按钮Selector
            # 注意：抖音页面结构可能变化，需要动态调整
            like_selectors = [
                'div[data-e2e="like-icon"]',
                '.like-icon',
                '[class*="like"] svg',
                'div[class*="like"]',
            ]
            
            for selector in like_selectors:
                try:
                    like_btn = await self.page.query_selector(selector)
                    if like_btn:
                        await like_btn.click()
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"[{self.account_name}] 点赞失败: {e}")
            return False
    
    def stop(self):
        """停止挂机"""
        self.running = False
        if self.browser:
            asyncio.create_task(self.browser.close())
    
    def _update_status(self, status):
        """更新账号状态"""
        conn = get_connection()
        conn.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, self.account_id))
        conn.commit()
        conn.close()
    
    def _log(self, action, message):
        """记录日志"""
        conn = get_connection()
        conn.execute(
            "INSERT INTO logs (account_id, action, message) VALUES (?, ?, ?)",
            (self.account_id, action, message)
        )
        conn.commit()
        conn.close()


# 运行任务
async def run_task(account_id, room_id):
    """运行单个账号的任务"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取账号信息
    cursor.execute("SELECT id, name, cookies_file FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"账号 {account_id} 不存在")
        return
    
    account_id, name, cookies_file = row
    conn.close()
    
    runner = LiveRoomRunner(account_id, name, cookies_file)
    await runner.start(room_id)


if __name__ == "__main__":
    # 测试
    asyncio.run(run_task(1, "123456"))
