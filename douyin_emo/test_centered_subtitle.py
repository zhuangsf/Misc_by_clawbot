#!/usr/bin/env python3
"""测试居中字幕视频生成"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/douyin_emo')

from generator.video_assembler import VideoAssembler
from generator.tts_wrapper import TTSManager
import asyncio

TEST_TEXT = "不是他看不懂你，是他不想懂。"

async def main():
    # 生成 TTS 语音
    tts = TTSManager()
    print(f"1. 生成语音: {TEST_TEXT}")
    audio_path = tts.text_to_speech(
        text=TEST_TEXT,
        voice="zh-CN-XiaoxiaoNeural",  # 传 voice name
        output_filename="test_centered"
    )
    
    # 生成视频
    assembler = VideoAssembler()
    print(f"2. 生成视频...")
    video = assembler.create_simple_video(
        text=TEST_TEXT,
        audio_path=audio_path,
        output_filename='subtitle_centered_test',
        duration=15.0
    )
    print(f"✅ 视频生成: {video}")
    
    # 清理临时语音
    import os
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print("  临时语音已清理")

if __name__ == "__main__":
    asyncio.run(main())
