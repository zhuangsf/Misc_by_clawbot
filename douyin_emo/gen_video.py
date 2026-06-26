#!/usr/bin/env python3
"""
抖音EMO视频生成器 - 快速生成脚本
用法: python3 gen_video.py <序号>

示例:
    python3 gen_video.py 003
    python3 gen_video.py 028
    python3 gen_video.py 003 028 053 078  (批量生成)
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from generator.tts_wrapper import TTSManager
from generator.video_assembler import VideoAssembler


def get_hook_text(video_id: int) -> tuple:
    """从数据库获取对应序号的文案"""
    import sqlite3
    
    conn = sqlite3.connect(str(PROJECT_ROOT / "database" / "hooks.db"))
    cursor = conn.cursor()
    
    cursor.execute("SELECT hook_type, full_text FROM hooks WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0], row[1]
    return None, None


def generate_video(video_id: str) -> bool:
    """生成单个视频"""
    try:
        vid = int(video_id)
    except ValueError:
        print(f"❌ 错误: '{video_id}' 不是有效的数字序号")
        return False
    
    # 获取文案
    hook_type, text = get_hook_text(vid)
    
    if not text:
        print(f"❌ 错误: 序号 {video_id} 不存在")
        return False
    
    print(f"\n{'='*50}")
    print(f"序号: {video_id}")
    print(f"类型: {hook_type}")
    print(f"文案: {text[:50]}...")
    print(f"{'='*50}")
    
    # 初始化模块
    tts = TTSManager(output_dir=str(PROJECT_ROOT / "output" / "audio"))
    assembler = VideoAssembler(output_dir=str(PROJECT_ROOT / "output" / "videos"))
    
    # 1. 生成音频
    print(f"[1/2] 生成音频...")
    audio_path = tts.text_to_speech(
        text=text,
        voice="zh-CN-XiaoxiaoNeural",
        output_filename=video_id
    )
    
    # 2. 生成视频
    print(f"[2/2] 生成视频...")
    duration = tts.estimate_duration(text)
    video_path = assembler.create_simple_video(
        text=text,
        audio_path=audio_path,
        output_filename=video_id,
        duration=min(duration, 15.0)
    )
    
    size = os.path.getsize(video_path)
    print(f"\n✅ 成功! {video_id}.mp4 ({size} bytes)")
    print(f"   视频路径: {video_path}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        
        # 显示可用的序号
        print("\n可用的序号范围:")
        print("  001-025  speak_for_me (替我说)")
        print("  026-050  resonate_with_me (与我同频)")
        print("  051-075  harsh_truths (扎心真相)")
        print("  076-100  open_endings (留白召唤)")
        
        # 检查已存在的视频
        video_dir = PROJECT_ROOT / "output" / "videos"
        if video_dir.exists():
            existing = sorted([f.stem for f in video_dir.glob("[0-9]*.mp4")])
            if existing:
                print(f"\n已生成的视频: {', '.join(existing)}")
        
        return
    
    # 解析参数
    video_ids = []
    for arg in sys.argv[1:]:
        if arg.isdigit() and len(arg) <= 3:
            # 补齐为3位数字
            video_ids.append(arg.zfill(3))
        else:
            video_ids.append(arg)
    
    # 批量生成
    success = 0
    failed = 0
    
    for vid in video_ids:
        if generate_video(vid):
            success += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"完成: {success} 成功, {failed} 失败")


if __name__ == "__main__":
    main()
