#!/usr/bin/env python3
"""
Volume Spikes SQLite数据库存储模块
替代文本文件，确保数据持久化
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "/root/.openclaw/workspace/volume_spikes.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volume_spikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            kline_time TEXT NOT NULL,
            symbol TEXT NOT NULL,
            volume REAL NOT NULL,
            volume_ratio REAL NOT NULL,
            price_direction TEXT,
            price_change_percent REAL,
            price_change REAL,
            previous_volume REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kline_time ON volume_spikes(kline_time);
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_symbol ON volume_spikes(symbol);
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_volume_ratio ON volume_spikes(volume_ratio);
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")

def add_record(data: Dict) -> int:
    """
    添加一条放量记录
    
    Args:
        data: 记录数据字典
    
    Returns:
        int: 新记录的ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO volume_spikes 
        (timestamp, kline_time, symbol, volume, volume_ratio, 
         price_direction, price_change_percent, price_change, previous_volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('timestamp', datetime.now().isoformat()),
        data.get('kline_time'),
        data.get('symbol'),
        data.get('volume'),
        data.get('volume_ratio'),
        data.get('price_direction'),
        data.get('price_change_percent'),
        data.get('price_change'),
        data.get('previous_volume')
    ))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ 记录已保存: ID={record_id}, {data.get('symbol')}, {data.get('volume_ratio')}倍")
    return record_id

def get_records(limit: int = 100, symbol: str = None) -> List[Dict]:
    """
    获取放量记录
    
    Args:
        limit: 最大返回数量
        symbol: 可选，按交易对过滤
    
    Returns:
        List[Dict]: 记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute('''
            SELECT id, timestamp, kline_time, symbol, volume, volume_ratio,
                   price_direction, price_change_percent, price_change, previous_volume, created_at
            FROM volume_spikes
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol, limit))
    else:
        cursor.execute('''
            SELECT id, timestamp, kline_time, symbol, volume, volume_ratio,
                   price_direction, price_change_percent, price_change, previous_volume, created_at
            FROM volume_spikes
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        records.append({
            'id': row[0],
            'timestamp': row[1],
            'kline_time': row[2],
            'symbol': row[3],
            'volume': row[4],
            'volume_ratio': row[5],
            'price_direction': row[6],
            'price_change_percent': row[7],
            'price_change': row[8],
            'previous_volume': row[9],
            'created_at': row[10]
        })
    
    return records

def get_statistics() -> Dict:
    """获取统计数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # 总记录数
    cursor.execute('SELECT COUNT(*) FROM volume_spikes')
    stats['total_count'] = cursor.fetchone()[0]
    
    # 按交易对统计
    cursor.execute('''
        SELECT symbol, COUNT(*) as count, AVG(volume_ratio) as avg_ratio 
        FROM volume_spikes 
        GROUP BY symbol
    ''')
    stats['by_symbol'] = {row[0]: {'count': row[1], 'avg_ratio': row[2]} for row in cursor.fetchall()}
    
    # 涨跌幅统计
    cursor.execute('''
        SELECT 
            COUNT(CASE WHEN price_change_percent > 0 THEN 1 END) as up_count,
            COUNT(CASE WHEN price_change_percent < 0 THEN 1 END) as down_count,
            AVG(price_change_percent) as avg_change
        FROM volume_spikes
    ''')
    row = cursor.fetchone()
    stats['up_count'] = row[0] or 0
    stats['down_count'] = row[1] or 0
    stats['avg_price_change'] = row[2] or 0
    
    conn.close()
    return stats

def migrate_from_log(log_file: str):
    """从日志文件迁移数据到数据库"""
    if not os.path.exists(log_file):
        print(f"⚠️ 文件不存在: {log_file}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                cursor.execute('''
                    INSERT OR IGNORE INTO volume_spikes 
                    (timestamp, kline_time, symbol, volume, volume_ratio, 
                     price_direction, price_change_percent, price_change, previous_volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp'),
                    data.get('kline_time'),
                    data.get('symbol'),
                    data.get('volume'),
                    data.get('volume_ratio'),
                    data.get('price_direction'),
                    data.get('price_change_percent'),
                    data.get('price_change'),
                    data.get('previous_volume')
                ))
                count += 1
            except json.JSONDecodeError:
                continue
    
    conn.commit()
    conn.close()
    print(f"✅ 从 {log_file} 迁移了 {count} 条记录")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Volume Spikes 数据库管理')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--migrate', type=str, help='从日志文件迁移数据')
    parser.add_argument('--list', action='store_true', help='列出所有记录')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--symbol', type=str, help='按交易对过滤')
    parser.add_argument('--limit', type=int, default=20, help='限制返回数量')
    
    args = parser.parse_args()
    
    if args.init:
        init_db()
    
    elif args.migrate:
        migrate_from_log(args.migrate)
    
    elif args.list:
        records = get_records(limit=args.limit, symbol=args.symbol)
        print(f"\n📊 放量记录 (共 {len(records)} 条):")
        for r in records:
            print(f"  {r['kline_time']} | {r['symbol']} | {r['volume_ratio']:.2f}倍 | {r['price_change_percent']:.2f}%")
    
    elif args.stats:
        stats = get_statistics()
        print(f"\n📈 统计信息:")
        print(f"  总记录数: {stats['total_count']}")
        print(f"  上涨次数: {stats['up_count']}")
        print(f"  下跌次数: {stats['down_count']}")
        print(f"  平均涨跌幅: {stats['avg_price_change']:.2f}%")
        for symbol, data in stats['by_symbol'].items():
            print(f"  {symbol}: {data['count']}条, 平均倍数 {data['avg_ratio']:.2f}")
    
    else:
        # 默认初始化
        init_db()
