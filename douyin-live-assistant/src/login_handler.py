"""
扫码登录模块 - 使用手机扫码方式
"""
import json
import os
import base64
import threading
from pathlib import Path
from flask import Blueprint, jsonify

login_bp = Blueprint('login', __name__)

BASE_DIR = Path(__file__).parent.parent
COOKIES_DIR = BASE_DIR / "cookies"


def render_login_page(account_id):
    """渲染登录页面HTML"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>抖音扫码登录 - 账号{account_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .box {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .input-group {{ margin: 15px 0; }}
            .input-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .input-group input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }}
            .btn {{ padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px; }}
            .btn:hover {{ background: #0056b3; }}
            .btn-success {{ background: #28a745; }}
            .tips {{ color: #666; font-size: 14px; margin-top: 15px; text-align: left; }}
            .tips ol {{ padding-left: 20px; }}
            .result {{ padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .success {{ background: #d4edda; color: #155724; }}
            .error {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 抖音扫码登录</h1>
            <p>账号ID: {account_id}</p>
            
            <div class="box">
                <h3>方法一：手机扫码（推荐）</h3>
                <p style="color: #666;">点击下方按钮生成二维码，然后用抖音APP扫描</p>
                <button class="btn" onclick="generateQR()">生成二维码</button>
                <div id="qrcode"></div>
            </div>
            
            <div class="box">
                <h3>方法二：手动导入Cookies</h3>
                <div class="tips">
                    <ol>
                        <li>在电脑浏览器登录抖音网页版 (douyin.com)</li>
                        <li>按 F12 打开开发者工具</li>
                        <li>切换到 Application/Application → Cookies</li>
                        <li>复制所有cookie（名称和值）</li>
                        <li>粘贴到下方文本框</li>
                        <li>点击"导入Cookies"</li>
                    </ol>
                </div>
                <div class="input-group">
                    <label>Cookies 文本（JSON格式）</label>
                    <textarea id="cookiesText" rows="6" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;" placeholder='[{{"name": "cookie名称", "value": "cookie值"}}, ...]'></textarea>
                </div>
                <button class="btn btn-success" onclick="importCookies()">导入Cookies</button>
            </div>
            
            <div id="result"></div>
        </div>
        
        <script>
            const accountId = {account_id};
            
            function generateQR() {{
                document.getElementById('qrcode').innerHTML = '<p>正在获取二维码...</p>';
                
                fetch('/login/generate_qr_simple/' + accountId)
                    .then(r => r.json())
                    .then(data => {{
                        if (data.code === 0) {{
                            document.getElementById('qrcode').innerHTML = '<img src="' + data.qr_image + '" style="max-width: 250px;">';
                        }} else {{
                            document.getElementById('qrcode').innerHTML = '<p style="color: red;">获取失败: ' + data.message + '</p>';
                        }}
                    }});
            }}
            
            function importCookies() {{
                const text = document.getElementById('cookiesText').value;
                if (!text) {{
                    alert('请输入Cookies');
                    return;
                }}
                
                fetch('/login/import_cookies/' + accountId, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{cookies_text: text}})
                }})
                .then(r => r.json())
                .then(data => {{
                    const result = document.getElementById('result');
                    if (data.code === 0) {{
                        result.innerHTML = '<div class="result success">✅ ' + data.message + '</div>';
                    }} else {{
                        result.innerHTML = '<div class="result error">❌ ' + data.message + '</div>';
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html


@login_bp.route('/login/<int:account_id>')
def show_login_page(account_id):
    """显示登录页面"""
    return render_login_page(account_id)


@login_bp.route('/login/generate_qr_simple/<int:account_id>')
def generate_qr_simple(account_id):
    """简单的二维码生成 - 返回一个示例二维码"""
    import qrcode
    import io
    
    # 生成登录URL的二维码
    login_url = "https://safelist.douyin.com/ls/?" + str(account_id)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(login_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 转为base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({
        "code": 0,
        "qr_image": f"data:image/png;base64,{img_str}",
        "message": "请用抖音APP扫描二维码授权"
    })


@login_bp.route('/login/import_cookies/<int:account_id>', methods=['POST'])
def import_cookies(account_id):
    """导入Cookies"""
    from flask import request
    data = request.json
    cookies_text = data.get('cookies_text', '')
    
    try:
        # 解析JSON
        cookies = json.loads(cookies_text)
        
        # 保存到文件
        cookies_file = COOKIES_DIR / f"account_{account_id}.json"
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        # 更新数据库
        from models import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE accounts SET cookies_file = ?, status = 'online' WHERE id = ?",
            (str(cookies_file), account_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "code": 0,
            "message": "Cookies导入成功！请刷新页面"
        })
        
    except json.JSONDecodeError:
        return jsonify({
            "code": 1,
            "message": "JSON格式解析失败，请检查格式"
        })
    except Exception as e:
        return jsonify({
            "code": 1,
            "message": str(e)
        })


@login_bp.route('/login/check/<int:account_id>')
def check_login(account_id):
    """检查登录状态"""
    cookies_file = COOKIES_DIR / f"account_{account_id}.json"
    if cookies_file.exists():
        return jsonify({"code": 0, "logged_in": True})
    return jsonify({"code": 0, "logged_in": False})
