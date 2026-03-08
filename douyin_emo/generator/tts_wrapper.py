"""
Edge TTS 语音合成 Wrapper
免费且支持多种中文声音
"""

import asyncio
import edge_tts
from pathlib import Path
from typing import Optional
import os
import re


class TTSManager:
    """
    Edge TTS 语音管理器
    
    推荐的中文女声：
    - 晓晓 (Xiaoxiao) - 温柔可爱
    - 晓辰 (Xiaochen) - 知性御姐
    - 云希 (Yunxi) - 磁性温柔
    - 晓睿 (Xiaorui) - 知性
    - 艾飞 (Fei) - 温柔女声
    """
    
    VOICES = {
        "温柔御姐": {
            "name": "zh-CN-XiaochenNeural",
            "description": "知性御姐音，温柔成熟"
        },
        "温柔可爱": {
            "name": "zh-CN-XiaoxiaoNeural", 
            "description": "温柔可爱，适合治愈系"
        },
        "磁性温柔": {
            "name": "zh-CN-YunxiNeural",
            "description": "磁性温柔男声"
        },
        "知性女声": {
            "name": "zh-CN-XiaoruiNeural",
            "description": "知性女声，清晰温柔"
        },
        "治愈女声": {
            "name": "zh-CN-AiFeiNeural",
            "description": "温柔治愈，适合情感类"
        }
    }
    
    # 默认使用"温柔御姐"风格
    DEFAULT_VOICE = "zh-CN-XiaochenNeural"
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or self._get_default_dir())
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_default_dir(self) -> str:
        return str(Path(__file__).parent / ".." / "output" / "audio")

    def clean_text_for_tts(self, text: str) -> str:
        """
        清理文本中的特殊符号（用于TTS）
        
        规则：
        - 移除 # 及其后的内容（话题标签）
        - 移除 @ 及其后的内容（提及）
        - 保留中文标点（，。！？：；）等
        - 移除其他特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        lines = []
        for line in text.split('\n'):
            # 移除 # 及其后的内容（话题标签）
            if '#' in line:
                line = line.split('#')[0]
            # 移除 @ 及其后的内容（提及）
            if '@' in line:
                line = line.split('@')[0]
            # 移除其他特殊字符，但保留中文标点
            line = re.sub(r'[#$@%^&*()_\-+=\[\]{}|\\<>,.?/~`]', '', line)
            # 清理多余空格
            line = line.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines)

    async def _generate_audio(
        self,
        text: str,
        voice: str,
        output_path: str,
        rate: str = "+0%",      # 语速：-50%到+50%
        volume: str = "+0%"     # 音量：-50%到+50%
    ):
        """
        异步生成音频
        
        Args:
            text: 要转换的文字
            voice: 声音名称
            output_path: 输出文件路径
            rate: 语速调整，如 "+0%", "+10%", "-10%"
            volume: 音量调整
        """
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output_path)

    def text_to_speech(
        self,
        text: str,
        voice: str = None,
        output_filename: str = None,
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> str:
        """
        文字转语音（同步接口）
        
        Args:
            text: 要转换的文字
            voice: 声音选择（支持名称或VOICES中的key）
            output_filename: 输出文件名（不含扩展名）
            rate: 语速调整
            volume: 音量调整
            
        Returns:
            生成的文件路径
        """
        voice = voice or self.DEFAULT_VOICE
        
        # 如果传入的是中文key，转换为voice name
        if voice in self.VOICES:
            voice = self.VOICES[voice]["name"]
        
        if not output_filename:
            import hashlib
            import time
            timestamp = int(time.time() * 1000)
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_filename = f"tts_{text_hash}_{timestamp}"
        
        output_path = self.output_dir / f"{output_filename}.mp3"
        
        # 清理文本（移除 # 等特殊符号，避免TTS读出来）
        clean_text = self.clean_text_for_tts(text)
        
        # 运行异步生成（使用清理后的文本）
        asyncio.run(self._generate_audio(
            text=clean_text,
            voice=voice,
            output_path=str(output_path),
            rate=rate,
            volume=volume
        ))
        
        return str(output_path)

    def get_available_voices(self) -> dict:
        """获取可用声音列表"""
        return {
            name: info["description"] 
            for name, info in self.VOICES.items()
        }

    def estimate_duration(self, text: str, rate: str = "+0%") -> float:
        """
        估算语音时长
        
        Args:
            text: 文本
            rate: 语速调整
            
        Returns:
            估算秒数
        """
        # 粗略估算：中文约3-4字/秒
        char_count = len(text)
        
        # 语速调整
        rate_value = 0
        if rate.startswith("+"):
            rate_value = int(rate[1:-1].replace("%", ""))
        elif rate.startswith("-"):
            rate_value = -int(rate[1:-1].replace("%", ""))
        
        # 基础速度：3.5字/秒
        base_speed = 3.5
        speed = base_speed * (1 + rate_value / 100)
        
        return char_count / speed


# 测试
if __name__ == "__main__":
    import sys
    
    tts = TTSManager()
    
    # 显示可用声音
    print("可用声音:")
    for name, desc in tts.get_available_voices().items():
        print(f"  - {name}: {desc}")
    
    # 测试语音生成
    test_texts = [
        "有些话你从来不说，但有人懂。",
        "凌晨三点，你也在等一个人的消息吗？",
        "其实你心里清楚，只是不想承认。"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n[{i+1}] 测试文本: {text}")
        
        # 使用默认声音
        output = tts.text_to_speech(
            text=text,
            output_filename=f"test_{i+1}"
        )
        
        # 估算时长
        estimated = tts.estimate_duration(text)
        print(f"  生成文件: {output}")
        print(f"  估算时长: {estimated:.2f}秒")
        
        # 使用另一种声音测试
        output2 = tts.text_to_speech(
            text=text,
            voice="zh-CN-XiaoxiaoNeural",
            output_filename=f"test_{i+1}_xiaoxiao"
        )
        print(f"  晓晓声音: {output2}")
