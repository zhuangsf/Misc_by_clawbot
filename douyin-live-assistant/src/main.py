"""
抖音直播挂机助手 - 主程序
"""
import os
import sys
from flask import Flask, jsonify, render_template
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入配置 - 使用相对导入
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config.config import HOST, PORT

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'douyin-live-assistant-2026'

# 注册蓝图
from account_manager import account_bp
from login_handler import login_bp
from task_manager import task_bp

app.register_blueprint(account_bp, url_prefix='/api')
app.register_blueprint(login_bp)
app.register_blueprint(task_bp, url_prefix='/api')

# 首页
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>抖音直播挂机助手</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            h1 { color: #333; text-align: center; }
            .container { background: white; padding: 30px; border-radius: 10px; }
            .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; 
                   text-decoration: none; border-radius: 5px; margin: 5px; }
            .btn:hover { background: #0056b3; }
            .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .status-online { color: green; }
            .status-offline { color: gray; }
        </style>
    </head>
    <body>
        <h1>🦞 抖音直播挂机助手</h1>
        <div class="container">
            <h2>功能导航</h2>
            <a href="/static/admin.html" class="btn">管理后台</a>
            <a href="/docs/TECH_PLAN.md" class="btn">技术文档</a>
            
            <h2>快速操作</h2>
            <a href="/api/accounts" class="btn">查看账号</a>
            <a href="/api/tasks" class="btn">查看任务</a>
            
            <h2>状态</h2>
            <div id="status">加载中...</div>
        </div>
        <script>
            fetch('/api/accounts')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').innerHTML = '账号数量: ' + data.data.length;
                });
        </script>
    </body>
    </html>
    '''


# 静态文件目录
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)


if __name__ == '__main__':
    print(f"🚀 抖音直播挂机助手启动中...")
    print(f"   访问地址: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
