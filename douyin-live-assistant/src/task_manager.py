"""
任务管理模块
"""
import asyncio
import json
import threading
from flask import Blueprint, request, jsonify
from models import get_connection

task_bp = Blueprint('tasks', __name__)

# 运行时任务存储
running_tasks = {}


@task_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, room_id, account_ids, status, created_at FROM tasks ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "room_id": row[1],
            "account_ids": json.loads(row[2]) if row[2] else [],
            "status": row[3],
            "created_at": row[4]
        })
    
    return jsonify({"code": 0, "data": tasks})


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建任务"""
    data = request.json
    room_id = data.get('room_id')
    account_ids = data.get('account_ids', [])
    
    if not room_id:
        return jsonify({"code": 1, "message": "缺少room_id"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (room_id, account_ids, status) VALUES (?, ?, ?)",
        (room_id, json.dumps(account_ids), 'stopped')
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"code": 0, "message": "任务创建成功", "task_id": task_id})


@task_bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动任务"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 获取任务信息
    cursor.execute("SELECT room_id, account_ids FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"code": 1, "message": "任务不存在"}), 404
    
    room_id, account_ids_json = row
    account_ids = json.loads(account_ids_json) if account_ids_json else []
    
    if not account_ids:
        conn.close()
        return jsonify({"code": 1, "message": "任务没有配置账号"}), 400
    
    # 更新任务状态
    conn.execute("UPDATE tasks SET status = 'running' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    # 启动异步任务
    def run():
        asyncio.run(_run_accounts(account_ids, room_id, task_id))
    
    thread = threading.Thread(target=run)
    thread.start()
    
    running_tasks[task_id] = {"room_id": room_id, "thread": thread}
    
    return jsonify({"code": 0, "message": "任务已启动"})


@task_bp.route('/tasks/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务"""
    if task_id in running_tasks:
        del running_tasks[task_id]
    
    conn = get_connection()
    conn.execute("UPDATE tasks SET status = 'stopped' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"code": 0, "message": "任务已停止"})


async def _run_accounts(account_ids, room_id, task_id):
    """运行账号挂机"""
    from executor.live_runner import run_task
    
    # 为每个账号创建任务
    tasks = []
    for account_id in account_ids:
        tasks.append(run_task(account_id, room_id))
    
    # 并发执行
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # 任务结束
    conn = get_connection()
    conn.execute("UPDATE tasks SET status = 'stopped' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
