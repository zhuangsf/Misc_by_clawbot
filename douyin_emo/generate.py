"""
抖音EMO视频生成器 - 主脚本
整合钩子生成、TTS、视频组装，批量生成15秒视频
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.hook_engine import HookEngine
from core.qianfan_client import QianfanClient
from generator.tts_wrapper import TTSManager
from generator.bgm_manager import BGMManager
from generator.video_assembler import VideoAssembler


class EMOVideoGenerator:
    """
    EMO视频生成器
    
    使用流程：
    1. 从钩子库获取/生成文案
    2. TTS转语音
    3. 匹配BGM
    4. 合成视频
    5. 输出到草稿箱
    """

    def __init__(
        self,
        project_root: str = None,
        llm_client = None
    ):
        self.project_root = Path(project_root or PROJECT_ROOT)
        
        # 初始化各模块
        self.hook_engine = HookEngine(db_path=str(self.project_root / "database" / "hooks.db"))
        self.tts = TTSManager(output_dir=str(self.project_root / "output" / "audio"))
        self.bgm = BGMManager(music_dir=str(self.project_root / "music" / "hot_bgm"))
        self.assembler = VideoAssembler(output_dir=str(self.project_root / "output" / "videos"))
        
        # LLM客户端（可选）
        self.llm = llm_client

    def generate_one(
        self,
        hook_type: str = None,
        use_llm: bool = False,
        emotion: str = "emo",
        voice: str = "zh-CN-XiaochenNeural"
    ) -> Dict:
        """
        生成一条视频
        
        Args:
            hook_type: 钩子类型（None则随机）
            use_llm: 是否使用LLM生成新钩子
            emotion: 匹配BGM的情绪类型
            voice: TTS声音
            
        Returns:
            生成结果信息
        """
        result = {
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "hook_type": hook_type,
            "emotion": emotion
        }
        
        # 1. 获取/生成钩子（完整15秒结构）
        if use_llm and self.llm:
            print("[Generator] 使用LLM生成新钩子...")
            hook_data = self.hook_engine.get_full_hook_with_comments(hook_type or "speak_for_me")
            
            if not hook_data:
                template_hook = self.hook_engine.get_random_hook(hook_type)
            
            if hook_data:
                # 使用LLM生成的完整钩子
                hook_text = hook_data.get("full_text", "") or hook_data.get("hook", "")
                result["hook_type"] = hook_data.get("type", hook_type)
                result["source"] = "llm"
            else:
                # 回退到模板
                template_hook = self.hook_engine.get_random_hook(hook_type)
                hook_text = template_hook.get("full_text", "") if template_hook else ""
                result["source"] = "template"
        else:
            # 使用模板获取完整钩子
            hook_data = self.hook_engine.get_full_hook(hook_type)
            
            if hook_data:
                hook_text = hook_data.get("full_text", "")
                result["hook_type"] = hook_data.get("type", hook_type)
                result["source"] = "template"
                result["hook_data"] = hook_data
            else:
                hook_text = ""
        
        if not hook_text:
            result["status"] = "error"
            result["error"] = "无法获取钩子"
            return result
        
        result["hook_content"] = hook_text
        print(f"[Generator] 钩子类型: {result['hook_type']}")
        
        # 使用完整文本作为字幕内容
        subtitle_text = hook_text
        
        # 2. TTS语音（使用完整文本）
        print(f"[Generator] 生成语音...")
        audio_path = self.tts.text_to_speech(
            text=subtitle_text,
            voice=voice,
            output_filename=f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        result["audio_path"] = audio_path
        
        # 估算时长
        duration = self.tts.estimate_duration(subtitle_text)
        result["duration"] = duration
        print(f"[Generator] 语音时长: {duration:.2f}秒")
        
        # 3. 匹配BGM（暂不混合，只记录）
        print(f"[Generator] 匹配BGM ({emotion})...")
        bgm_info = self.bgm.get_random_bgm(emotion)
        
        if bgm_info:
            bgm_path = bgm_info["file"]
            result["bgm_info"] = {
                "name": bgm_info["name"],
                "emotion": bgm_info["emotion"]
            }
            print(f"[Generator] BGM: {bgm_info['name']}")
            print(f"[Generator] 注意: 当前版本暂不支持BGM+字幕混合，将只生成语音+字幕版本")
        else:
            bgm_path = None
            result["bgm_info"] = None
            print("[Generator] 无BGM，直接生成语音+字幕")
        
        # 4. 生成带字幕的视频
        print(f"[Generator] 生成视频...")
        video_path = self.assembler.create_simple_video(
            text=subtitle_text,  # 完整文本作为字幕
            audio_path=audio_path,
            output_filename=f"emo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            duration=min(duration, 15.0),
            bgm_path=bgm_path
        )
        
        result["video_path"] = video_path
        result["status"] = "success"
        
        print(f"[Generator] 完成: {video_path}")
        
        return result

    def generate_batch(
        self,
        count: int = 5,
        hook_types: List[str] = None,
        emotions: List[str] = None,
        voice: str = "zh-CN-XiaochenNeural"
    ) -> List[Dict]:
        """
        批量生成视频
        
        Args:
            count: 生成数量
            hook_types: 钩子类型列表（None则随机）
            emotions: 情绪类型列表
            voice: TTS声音
            
        Returns:
            生成结果列表
        """
        results = []
        
        # 默认值
        hook_types = hook_types or ["speak_for_me", "resonate_with_me", "harsh_truths", "open_endings"]
        emotions = emotions or ["emo", "扎心", "治愈", "搞笑"]
        
        print(f"="*50)
        print(f"开始批量生成 {count} 条视频")
        print(f"钩子类型: {hook_types}")
        print(f"情绪类型: {emotions}")
        print(f"声音: {voice}")
        print(f"="*50)
        
        for i in range(count):
            print(f"\n[{i+1}/{count}] 生成中...")
            
            # 轮换使用不同类型
            hook_type = hook_types[i % len(hook_types)]
            emotion = emotions[i % len(emotions)]
            
            result = self.generate_one(
                hook_type=hook_type,
                use_llm=False,  # 批量时先用模板
                emotion=emotion,
                voice=voice
            )
            
            results.append(result)
            
            if result["status"] == "success":
                print(f"  ✓ {result['hook_content'][:30]}...")
            else:
                print(f"  ✗ 失败: {result.get('error', '未知错误')}")
        
        # 输出统计
        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n{'='*50}")
        print(f"批量生成完成: {success_count}/{count} 成功")
        print(f"="*50)
        
        return results

    def save_manifest(self, results: List[Dict], manifest_path: str = None):
        """
        保存生成清单
        
        Args:
            results: 生成结果列表
            manifest_path: 清单文件路径
        """
        manifest_path = manifest_path or str(self.project_root / "output" / "manifest.json")
        
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "videos": []
        }
        
        for r in results:
            if r["status"] == "success":
                manifest["videos"].append({
                    "timestamp": r["timestamp"],
                    "hook_type": r["hook_type"],
                    "content": r["hook_content"],
                    "hook": r["hook_content"],
                    "audio": r.get("audio_path", ""),
                    "video": r["video_path"],
                    "bgm": r.get("bgm_info", {}),
                    "duration": r.get("duration", 0)
                })
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"[Generator] 清单已保存: {manifest_path}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="抖音EMO视频生成器")
    parser.add_argument("--count", type=int, default=3, help="生成数量")
    parser.add_argument("--hook-type", type=str, default=None, help="钩子类型")
    parser.add_argument("--emotion", type=str, default="emo", help="情绪类型")
    parser.add_argument("--voice", type=str, default="zh-CN-XiaochenNeural", help="TTS声音")
    parser.add_argument("--use-llm", action="store_true", help="使用LLM生成新钩子")
    parser.add_argument("--llm-key", type=str, help="千帆API Key")
    
    args = parser.parse_args()
    
    # 初始化LLM客户端（如果需要）
    llm_client = None
    if args.use_llm:
        try:
            api_key = args.llm_key or os.getenv("QIANFAN_API_KEY") or os.getenv("BAIDU_API_KEY")
            llm_client = QianfanClient(api_key=api_key)
            print("[Main] LLM客户端已连接")
        except Exception as e:
            print(f"[Main] LLM连接失败: {e}")
            print("[Main] 将使用模板生成")
    
    # 初始化生成器
    generator = EMOVideoGenerator(llm_client=llm_client)
    
    # 确保钩子模板已初始化
    print("[Main] 检查钩子库...")
    generator.hook_engine.seed_initial_templates()
    
    # 批量生成
    results = generator.generate_batch(
        count=args.count,
        emotions=[args.emotion],
        voice=args.voice
    )
    
    # 保存清单
    generator.save_manifest(results)
    
    # 打印结果
    print("\n生成结果:")
    for i, r in enumerate(results, 1):
        status = "✓" if r["status"] == "success" else "✗"
        content = r.get("hook_content", "")[:40]
        video = r.get("video_path", "")
        print(f"  {i}. {status} {content}")
        if video:
            print(f"     → {video}")


if __name__ == "__main__":
    main()
