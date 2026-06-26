"""
账号管理模块
"""
import json
import os
from pathlib import Path

from flask import Blueprint, request, jsonify
from models import get_connection

# 蓝图
account_bp = Blueprint('accounts', __name__)

BASE_DIR = Path(__file__).parent.parent.parent
COOKIES_DIR = BASE_DIR / "cookies"


@account_bp.route('/accounts', methods=['GET'])
def list_accounts():
    """获取账号列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status, proxy_url, created_at FROM accounts ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    accounts = []
    for row in rows:
        accounts.append({
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "proxy_url": row[3],
            "created_at": row[4]
        })
    
    return jsonify({"code": 0, "data": accounts})


@account_bp.route('/accounts', methods=['POST'])
def add_account():
    """添加账号"""
    data = request.json
    name = data.get('name', f'账号{len(get_accounts()) + 1}')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO accounts (name, status) VALUES (?, ?)",
        (name, 'offline')
    )
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"code": 0, "message": "账号添加成功", "account_id": account_id})


@account_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """删除账号"""
    conn = get_connection()
    
    # 获取cookies文件路径
    cursor = conn.cursor()
    cursor.execute("SELECT cookies_file FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    
    if row and row[0] and os.path.exists(row[0]):
        os.remove(row[0])
    
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"code": 0, "message": "账号删除成功"})


@account_bp.route('/accounts/<int:account_id>/login', methods=['POST'])
def trigger_login(account_id):
    """触发扫码登录"""
    # 返回扫码页面URL
    return jsonify({
        "code": 0, 
        "data": {
            "login_url": f"/login/{account_id}",
            "message": "请访问该页面扫码登录"
        }
    })


@account_bp.route('/accounts/<int:account_id>/status', methods=['PUT'])
def update_status(account_id):
    """更新账号状态"""
    data = request.json
    status = data.get('status')
    
    conn = get_connection()
    conn.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
    conn.commit()
    conn.close()
    
    return jsonify({"code": 0, "message": "状态更新成功"})


def get_accounts():
    """获取所有账号"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status FROM accounts")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "status": r[2]} for r in rows]
