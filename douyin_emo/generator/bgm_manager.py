"""
背景音乐管理器
管理热门BGM下载和分类
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import os


class BGMManager:
    """
    背景音乐管理器
    
    功能：
    - BGM分类存储
    - 按情绪匹配
    - 下载管理
    """
    
    # 预定义的情绪分类（可直接使用抖音热门BGM）
    EMOTION_CATEGORIES = {
        "emo": {
            "description": "悲伤、失落、思念",
            "keywords": ["悲伤", "失恋", "思念", "孤独", "深夜"],
            "bpm_range": (60, 80)
        },
        "治愈": {
            "description": "温暖、治愈、被理解",
            "keywords": ["治愈", "温暖", "励志", "希望"],
            "bpm_range": (70, 100)
        },
        "能量": {
            "description": "积极、向上、有力量",
            "keywords": ["正能量", "励志", "燃", "热血"],
            "bpm_range": (100, 140)
        },
        "搞笑": {
            "description": "轻松、愉快、搞笑",
            "keywords": ["搞笑", "欢乐", "轻松", "沙雕"],
            "bpm_range": (90, 130)
        },
        "扎心": {
            "description": "扎心、反转、引发共鸣",
            "keywords": ["扎心", "破防", "真相", "现实"],
            "bpm_range": (70, 100)
        }
    }
    
    def __init__(self, music_dir: str = None):
        self.music_dir = Path(music_dir or self._get_default_dir())
        self.music_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.music_dir / "bgm_database.json"
        self.bgm_db = self._load_db()

    def _get_default_dir(self) -> str:
        return str(Path(__file__).parent / ".." / "music" / "hot_bgm")

    def _load_db(self) -> Dict:
        """加载BGM数据库"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"version": "1.0", "bgms": []}

    def _save_db(self):
        """保存BGM数据库"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.bgm_db, f, ensure_ascii=False, indent=2)

    def add_bgm(
        self,
        name: str,
        file_path: str,
        emotion: str = "emo",
        duration: float = None,
        bpm: int = None,
        description: str = ""
    ) -> str:
        """
        添加一条BGM
        
        Args:
            name: BGM名称
            file_path: 文件路径
            emotion: 情绪分类
            duration: 时长（秒）
            bpm: 节拍数
            description: 描述
            
        Returns:
            BGM ID
        """
        bgm_id = f"bgm_{len(self.bgm_db['bgms']) + 1}"
        
        bgm_info = {
            "id": bgm_id,
            "name": name,
            "file": str(Path(file_path).resolve()),
            "emotion": emotion,
            "duration": duration,
            "bpm": bpm,
            "description": description,
            "use_count": 0
        }
        
        self.bgm_db["bgms"].append(bgm_info)
        self._save_db()
        
        return bgm_id

    def get_random_bgm(self, emotion: str = None) -> Optional[Dict]:
        """
        随机获取一条BGM
        
        Args:
            emotion: 情绪分类过滤
            
        Returns:
            BGM信息字典
        """
        import random
        
        available = self.bgm_db["bgms"]
        
        if emotion:
            available = [b for b in available if b.get("emotion") == emotion]
        
        if not available:
            return None
        
        bgm = random.choice(available)
        bgm["use_count"] += 1
        self._save_db()
        
        return bgm

    def get_bgm_by_emotion(self, emotion: str) -> List[Dict]:
        """获取指定情绪的所有BGM"""
        return [b for b in self.bgm_db["bgms"] if b.get("emotion") == emotion]

    def list_emotions(self) -> List[str]:
        """列出所有情绪分类"""
        return list(self.EMOTION_CATEGORIES.keys())

    def get_emotion_info(self, emotion: str) -> Dict:
        """获取情绪分类详情"""
        return self.EMOTION_CATEGORIES.get(emotion, {})

    def get_bgm_stats(self) -> Dict:
        """获取BGM统计"""
        total = len(self.bgm_db["bgms"])
        emotion_count = {}
        
        for bgm in self.bgm_db["bgms"]:
            emo = bgm.get("emotion", "unknown")
            emotion_count[emo] = emotion_count.get(emo, 0) + 1
        
        return {
            "total": total,
            "by_emotion": emotion_count
        }

    def get_all_bgm(self) -> List[Dict]:
        """获取所有BGM列表"""
        return self.bgm_db["bgms"]


# 初始化示例（庄庄需要自己填充BGM）
def init_sample_bgm():
    """
    初始化示例BGM记录
    庄庄需要实际下载这些音乐文件
    """
    manager = BGMManager()
    
    # 示例：常见的抖音情感类BGM（庄庄需要实际添加）
    sample_bgms = [
        ("emo_01", "抖音热榜-悲伤01.mp3", "emo", 15, 70, "适合失恋、思念类文案"),
        ("emo_02", "抖音热榜-悲伤02.mp3", "emo", 15, 75, "适合深夜EMO"),
        ("heal_01", "抖音热榜-治愈01.mp3", "治愈", 15, 80, "温暖治愈"),
        ("zhixin_01", "抖音热榜-扎心01.mp3", "扎心", 15, 85, "扎心真相类"),
        ("zhixin_02", "抖音热榜-扎心02.mp3", "扎心", 15, 90, "破防类"),
    ]
    
    # 这里只是创建记录，实际文件需要庄庄下载
    print("[BGMManager] 请手动添加BGM文件到:", manager.music_dir)
    print("\n示例添加记录（需要实际文件）：")
    
    for name, filename, emotion, duration, bpm, desc in sample_bgms:
        print(f"  - {name}: {filename} ({emotion}) - {desc}")
    
    return manager


if __name__ == "__main__":
    manager = BGMManager()
    
    # 显示统计
    stats = manager.get_bgm_stats()
    print("BGM库状态:")
    print(f"  总数: {stats['total']}")
    print(f"  按情绪: {stats['by_emotion']}")
    
    # 列出情绪分类
    print("\n情绪分类:")
    for emo, info in manager.EMOTION_CATEGORIES.items():
        print(f"  - {emo}: {info['description']}")
    
    # 示例：获取随机BGM
    bgm = manager.get_random_bgm("emo")
    if bgm:
        print(f"\n随机emo BGM: {bgm['name']}")
    else:
        print("\n暂无BGM，请添加")
    
    print("\n" + "="*50)
    print("BGM文件存放目录:", manager.music_dir)
    print("请放入音乐文件后，使用 add_bgm() 添加记录")
