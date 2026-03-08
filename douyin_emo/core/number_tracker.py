#!/usr/bin/env python3
"""
抖音EMO视频编号追踪系统
确保文案、音频、视频三者的编号完全对应

编号规则：
- speak_for_me: 001-025
- resonate_with_me: 026-050
- harsh_truths: 051-075
- open_endings: 076-100
"""

import random
from typing import Dict, List, Optional

# 编号映射表
NUMBER_MAP = {
    # harsh_truths (扎心真相) - 编号 051-075
    "051": {
        "type": "harsh_truths",
        "content": "不是没人追你。是你不要。你嫌弃这个，看不上那个。#眼光太高"
    },
    "052": {
        "type": "harsh_truths", 
        "content": "其实不是忘不掉那个人。是你还不甘心。#不甘心"
    },
    "053": {
        "type": "harsh_truths",
        "content": "说白了。你不是没机会，你只是不敢。机会来了，你却缩回去了。#你不敢"
    },
    "054": {
        "type": "harsh_truths",
        "content": "你不是社恐。你只是没遇到感兴趣的人。遇到喜欢的，你比谁都主动。#只是没遇到对的人"
    },
    "055": {
        "type": "harsh_truths",
        "content": "其实你心里清楚。只是不想面对。自欺欺人，是最轻松的方式。#自欺欺人"
    },
    "056": {
        "type": "harsh_truths",
        "content": "不是他不好。是你习惯了更好。#别太贪心"
    },
    "057": {
        "type": "harsh_truths",
        "content": "你嘴上说随缘。其实比谁都急。#嘴上说随缘"
    },
    "058": {
        "type": "harsh_truths",
        "content": "不是生活太难。是你想得太多。#想太多"
    },
    "059": {
        "type": "harsh_truths",
        "content": "不是你不努力。是你方向错了。#方向比努力重要"
    },
    "060": {
        "type": "harsh_truths",
        "content": "其实你怕的不是失败。是丢人。#怕丢人"
    },
    "061": {
        "type": "harsh_truths",
        "content": "不是没人懂你。是你没给机会。#给机会让人懂你"
    },
    "062": {
        "type": "harsh_truths",
        "content": "你不是因为忙。是因为懒。#懒"
    },
    "063": {
        "type": "harsh_truths",
        "content": "不是感情变了。是你要求多了。#要求太多"
    },
    "064": {
        "type": "harsh_truths",
        "content": "不是他不懂浪漫。是你没说需要什么。#直接说"
    },
    "065": {
        "type": "harsh_truths",
        "content": "其实你不是因为喜欢他。你只是害怕孤独。#害怕孤独"
    },
    "066": {
        "type": "harsh_truths",
        "content": "不是你没时间。你只是不想做。#时间都去哪了"
    },
    "067": {
        "type": "harsh_truths",
        "content": "不是生活没意思。是你没意思。#让自己有意思"
    },
    "068": {
        "type": "harsh_truths",
        "content": "不是没人愿意懂你。是不愿被懂。#不愿被懂"
    },
    "069": {
        "type": "harsh_truths",
        "content": "不是梦想太远。是你不敢出发。#不敢出发"
    },
    "070": {
        "type": "harsh_truths",
        "content": "不是世界不公平。是你没努力。#努力"
    },
    "071": {
        "type": "harsh_truths",
        "content": "其实你都知道。只是不想做。#知行合一"
    },
    "072": {
        "type": "harsh_truths",
        "content": "不是你不成熟。是你不想长大。#不想长大"
    },
    "073": {
        "type": "harsh_truths",
        "content": "不是他不爱了。是你不爱了。#其实是你不爱了"
    },
    "074": {
        "type": "harsh_truths",
        "content": "不是圈子小。是你不出去。#走出去"
    },
    "075": {
        "type": "harsh_truths",
        "content": "不是没优点。是你自己不知道。#发现自己优点"
    },
    # ... 其他编号待添加
}


class NumberTracker:
    """编号追踪器"""
    
    def __init__(self, mapping_file: str = None):
        self.mapping = NUMBER_MAP.copy()
        self.used_numbers = set()
        
    def get_by_number(self, number: str) -> Optional[Dict]:
        """根据编号获取文案"""
        return self.mapping.get(number)
    
    def get_next_available(self) -> str:
        """获取下一个可用编号"""
        for i in range(1, 101):
            num = f"{i:03d}"
            if num not in self.used_numbers and num in self.mapping:
                return num
        return None
    
    def mark_used(self, number: str):
        """标记编号已使用"""
        self.used_numbers.add(number)
        
    def get_all_used(self) -> List[str]:
        """获取所有已使用的编号"""
        return sorted(list(self.used_numbers))
    
    def get_by_type(self, hook_type: str) -> List[Dict]:
        """获取指定类型的所有文案"""
        return [
            {"number": k, **v} 
            for k, v in self.mapping.items() 
            if v["type"] == hook_type
        ]


# 便捷函数
def get_content_by_number(number: str) -> Optional[str]:
    """根据编号获取文案内容"""
    return NUMBER_MAP.get(number, {}).get("content")


def get_type_by_number(number: str) -> Optional[str]:
    """根据编号获取类型"""
    return NUMBER_MAP.get(number, {}).get("type")


if __name__ == "__main__":
    tracker = NumberTracker()
    
    # 测试 053
    print("测试编号 053:")
    content_053 = get_content_by_number("053")
    type_053 = get_type_by_number("053")
    print(f"  内容: {content_053}")
    print(f"  类型: {type_053}")
    
    # 遍历 harsh_truths 类型
    print("\nharsh_truths 类型的文案 (051-075):")
    for k, v in sorted(tracker.get_by_type("harsh_truths")):
        print(f"  {k}: {v['content'][:50]}...")
