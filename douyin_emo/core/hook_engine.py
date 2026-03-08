"""
EMO共鸣系统 - 增强版钩子生成器
4种底层情感触发器生成器
完整15秒结构：Hook → 展开 → 峰值 → 留白
"""

import random
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import os


class HookEngine:
    """
    情感钩子生成器（增强版）
    
    4种核心钩子类型：
    1. speak_for_me - 替我说（说出用户心里话）
    2. resonate_with_me - 与我同频（描述她的状态）
    3. harsh_truths - 扎心真相（反常识洞察）
    4. open_endings - 留白召唤（让她补充）
    
    15秒完整结构：
    - 0-3秒：Hook（抓住注意力）
    - 3-8秒：展开（场景/细节铺垫）
    - 8-12秒：峰值（情绪高点/真相揭示）
    - 12-15秒：留白（引导评论区）
    """

    HOOK_TYPES = {
        "speak_for_me": {
            "description": "替用户说出她心里想说但没说出口的话",
            "keywords": ["替我说", "帮我说", "说出心里话"],
            "emotion": "被理解",
        },
        "resonate_with_me": {
            "description": "描述用户当下的状态，让她觉得'这说的就是我'",
            "keywords": ["你也", "其实你", "凌晨"],
            "emotion": "同频感",
        },
        "harsh_truths": {
            "description": "说出反常识的真相，扎心但真实",
            "keywords": ["不是", "其实", "说白了"],
            "emotion": "惊醒",
        },
        "open_endings": {
            "description": "留白不说全，让用户自己在评论区补充",
            "keywords": ["你们都懂", "我就不说了", "的那句话"],
            "emotion": "召唤",
        }
    }

    # 增强版钩子模板（完整15秒结构）
    TEMPLATES = {
        "speak_for_me": [
            {
                "hook": "你不是不想结婚。",
                "expand": "你只是还没遇到那个，让你甘心放弃自由的人。",
                "peak": "但如果遇到了，晚一点又有什么关系？",
                "ending": "#你们是遇到了，还是没遇到？"
            },
            {
                "hook": "有些话你从来不说。",
                "expand": "但不代表你不想被懂得。",
                "peak": "其实你比谁都渴望有个人，能看穿你的脆弱。",
                "ending": "#说了矫情，不说憋屈"
            },
            {
                "hook": "你不是没人追。",
                "expand": "你只是不想要那些敷衍的喜欢。",
                "peak": "你在等一个人，知你冷暖，懂你悲欢。",
                "ending": "#你们等到那个人了吗？"
            },
            {
                "hook": "你嘴上说没事。",
                "expand": "其实心里翻江倒海。",
                "peak": "你不是真的没事，你只是习惯了一个人扛。",
                "ending": "#谁不是一边崩溃一边假装没事"
            },
            {
                "hook": "你等的不是晚安。",
                "expand": "是安心。",
                "peak": "是一个能让你踏实入睡的拥抱。",
                "ending": "#晚安不重要，重要的是对谁说"
            },
            {
                "hook": "有些委屈。",
                "expand": "你从来不对任何人说。",
                "peak": "不是因为你不信任，是因为说出来也没用。",
                "ending": "#成年人的崩溃就在一瞬间"
            },
            {
                "hook": "你不是不够好。",
                "expand": "你只是没遇到对的人。",
                "peak": "别否定自己，你值得更好的。",
                "ending": "#值得被爱的人终会遇到对的人"
            },
            {
                "hook": "你删掉又打好的消息。",
                "expand": "最后还是没有发出去。",
                "peak": "因为你知道，有些话说了不如沉默。",
                "ending": "#你们有多少消息是打好又删掉的？"
            },
            {
                "hook": "你假装不在乎的样子。",
                "expand": "其实最让人心疼。",
                "peak": "因为你比谁都在乎，只是没人看见。",
                "ending": "#越假装越让人心疼"
            },
            {
                "hook": "有些痛。",
                "expand": "只有深夜才敢想。",
                "peak": "白天你是个正常人，晚上你才敢做自己。",
                "ending": "#一到深夜就EMO的你"
            },
            {
                "hook": "你不是一个人。",
                "expand": "你只是还没遇到同类。",
                "peak": "在这世界的某个角落，有人和你一样在等。",
                "ending": "#总会遇到的"
            },
            {
                "hook": "你的坚强。",
                "expand": "只是因为还没找到可以依靠的人。",
                "peak": "但你不需要永远坚强，偶尔软弱也是一种勇气。",
                "ending": "#允许自己软弱"
            },
            {
                "hook": "你不说。",
                "expand": "不代表不想要。",
                "peak": "有些渴望，说出来就输了。",
                "ending": "#成年人的世界"
            },
            {
                "hook": "你看起来没事。",
                "expand": "其实心里翻江倒海。",
                "peak": "成年人的崩溃，就是在这一瞬间。",
                "ending": "#谁都一样"
            },
            {
                "hook": "你不是不想努力。",
                "expand": "你是不知道为了什么。",
                "peak": "没有目标的努力，只是自我感动。",
                "ending": "#你找到目标了吗？"
            },
            {
                "hook": "你嘴上说算了。",
                "expand": "心里可没打算。",
                "peak": "有些事，不是说放就能放的。",
                "ending": "#说算了容易，放下难"
            },
            {
                "hook": "有些事。",
                "expand": "不是忘了，是不想提。",
                "peak": "那些伤疤，揭开了还是会疼。",
                "ending": "#有些事就让它过去吧"
            },
            {
                "hook": "你等的那个拥抱。",
                "expand": "其实可以自己给自己。",
                "peak": "但你缺的，从来不是拥抱。",
                "ending": "#缺的是那个人"
            },
            {
                "hook": "有些累。",
                "expand": "只有自己知道。",
                "peak": "你说没事的样子，让人更心疼。",
                "ending": "#成年人的世界没有容易二字"
            },
            {
                "hook": "你不是不想。",
                "expand": "你只是怕失望。",
                "peak": "期望越高，失望越痛。",
                "ending": "#怕失望所以不敢期待"
            },
            {
                "hook": "你不是社恐。",
                "expand": "你只是没遇到感兴趣的人。",
                "peak": "遇到喜欢的人，你比谁都主动。",
                "ending": "#只是没遇到对的人"
            },
            {
                "hook": "你心里有一句话。",
                "expand": "憋了很久了吧？",
                "peak": "有时候，说出来反而是一种解脱。",
                "ending": "#把话憋在心里会憋出病的"
            },
            {
                "hook": "其实你比谁都清楚。",
                "expand": "只是不想承认。",
                "peak": "自欺欺人，只是因为真相太疼。",
                "ending": "#真相往往很残忍"
            },
            {
                "hook": "你说的没事。",
                "expand": "其实心里有事。",
                "peak": "但你不想让任何人担心。",
                "ending": "#这就是长大"
            },
            {
                "hook": "有些话说了矫情。",
                "expand": "不说憋屈。",
                "peak": "这就是成年人的常态。",
                "ending": "#说与不说都难"
            },
        ],
        "resonate_with_me": [
            {
                "hook": "凌晨三点。",
                "expand": "你也在等一个人的消息吗？",
                "peak": "明明知道不会有回复，还是舍不得放下手机。",
                "ending": "#等消息等到凌晨的你"
            },
            {
                "hook": "你也是那种。",
                "expand": "在人群中突然就很想家的人吧？",
                "peak": "明明也没什么烦心事，但就是那一瞬间，鼻子一酸。",
                "ending": "#想家不需要理由"
            },
            {
                "hook": "你也是那种。",
                "expand": "表面坚强的人吧？",
                "peak": "只有晚上一个人的时候，才敢偷偷哭。",
                "ending": "#白天坚强，晚上脆弱"
            },
            {
                "hook": "你也是那种。",
                "expand": "明明很难过却笑着说没事的人吧？",
                "peak": "因为你知道，说出来也没人能帮你。",
                "ending": "#笑着笑着说没事"
            },
            {
                "hook": "你也是那种。",
                "expand": "一个人吃饭一个人看电影的人吧？",
                "peak": "不是没人陪，是不想迁就。",
                "ending": "#一个人也挺好"
            },
            {
                "hook": "你也是那种。",
                "expand": "晚上想的比白天多的人吧？",
                "peak": "白天太忙，只有深夜才属于自己。",
                "ending": "#一到晚上就多想"
            },
            {
                "hook": "你也是那种。",
                "expand": "听歌听到突然想哭的人吧？",
                "peak": "某一首歌，仿佛唱的就是你。",
                "ending": "#总有一首歌唱的是你"
            },
            {
                "hook": "你也是那种。",
                "expand": "想联系又不敢联系的人吧？",
                "peak": "害怕打扰，更害怕已读不回。",
                "ending": "#想联系又不敢联系"
            },
            {
                "hook": "你也是那种。",
                "expand": "明明很在意却装作不在乎吧？",
                "peak": "因为你觉得，先开口就输了。",
                "ending": "#装作不在乎的样子"
            },
            {
                "hook": "你也是那种。",
                "expand": "白天正常，晚上EMO的人吧？",
                "peak": "一到晚上就开始胡思乱想。",
                "ending": "#晚上EMO综合征"
            },
            {
                "hook": "你也是那种。",
                "expand": "看起来很忙其实很孤独吧？",
                "peak": "忙到没时间社交，但内心却渴望陪伴。",
                "ending": "#忙到没朋友"
            },
            {
                "hook": "你也是那种。",
                "expand": "明明很累却还撑着的人吧？",
                "peak": "因为你知道，倒下了没人帮你撑。",
                "ending": "#成年人的世界"
            },
            {
                "hook": "你也是那种。",
                "expand": "发泄消息撤回的人吧？",
                "peak": "打了一堆字，最后全部删除。",
                "ending": "#消息打好又撤回"
            },
            {
                "hook": "你也是那种。",
                "expand": "一个人在陌生的城市生活吗？",
                "peak": "孤独的时候，连呼吸都是冷的。",
                "ending": "#一个人在大城市"
            },
            {
                "hook": "你也是那种。",
                "expand": "期待什么又怕失望吧？",
                "peak": "期望越大，失望越痛。",
                "ending": "#怕失望所以不敢期待"
            },
            {
                "hook": "你也是那种。",
                "expand": "表面很酷心里很软吧？",
                "peak": "嘴上说着无所谓，心里却在意得要命。",
                "ending": "#外冷内热"
            },
            {
                "hook": "你也是那种。",
                "expand": "一个人扛着很多事吧？",
                "peak": "不想麻烦别人，所以什么都自己扛。",
                "ending": "#什么都要自己扛"
            },
            {
                "hook": "你也是那种。",
                "expand": "笑得很开心心里却有事吧？",
                "peak": "微笑面具戴久了，连真实的自己都忘了。",
                "ending": "#微笑抑郁症"
            },
            {
                "hook": "你也是那种。",
                "expand": "突然就很累的人吧？",
                "peak": "明明什么都没做，却感觉精疲力尽。",
                "ending": "#没由来的疲惫"
            },
            {
                "hook": "你也是那种。",
                "expand": "对生活失去热情的人吧？",
                "peak": "不是没有快乐，是快乐变得很贵。",
                "ending": "#快乐变得很奢侈"
            },
            {
                "hook": "你也是那种。",
                "expand": "在地铁上突然发呆的人吧？",
                "peak": "不知道在想什么，只是突然就空了。",
                "ending": "#突然就发呆"
            },
            {
                "hook": "你也是那种。",
                "expand": "不想社交只想宅着的人吧？",
                "peak": "不是没朋友，是社交太累。",
                "ending": "#社交恐惧症"
            },
            {
                "hook": "你也是那种。",
                "expand": "对什么都提不起兴趣的人吧？",
                "peak": "不是不想，是没动力。",
                "ending": "#动力缺失症"
            },
            {
                "hook": "你也是那种。",
                "expand": "突然就很丧的人吧？",
                "peak": "明明昨天还好好的，今天就不行了。",
                "ending": "#莫名的低落"
            },
            {
                "hook": "你也是那种。",
                "expand": "害怕一个人又习惯一个人吧？",
                "peak": "这种矛盾，只有自己懂。",
                "ending": "#矛盾的我们"
            },
        ],
        "harsh_truths": [
            {
                "hook": "不是没人追你。",
                "expand": "是你不要。",
                "peak": "你嫌弃这个，看不上那个。",
                "ending": "#眼光太高"
            },
            {
                "hook": "其实不是忘不掉那个人。",
                "expand": "是你还不甘心。",
                "peak": "不是因为爱，是因为投入太多。",
                "ending": "#不甘心"
            },
            {
                "hook": "说白了。",
                "expand": "你不是没机会，你只是不敢。",
                "peak": "机会来了，你却缩回去了。",
                "ending": "#你不敢"
            },
            {
                "hook": "你不是社恐。",
                "expand": "你只是没遇到感兴趣的人。",
                "peak": "遇到喜欢的，你比谁都主动。",
                "ending": "#只是没遇到对的人"
            },
            {
                "hook": "其实你心里清楚。",
                "expand": "只是不想面对。",
                "peak": "自欺欺人，是最轻松的方式。",
                "ending": "#自欺欺人"
            },
            {
                "hook": "不是他不好。",
                "expand": "是你习惯了更好。",
                "peak": "但更好的，不一定属于你。",
                "ending": "#别太贪心"
            },
            {
                "hook": "你嘴上说随缘。",
                "expand": "其实比谁都急。",
                "peak": "嘴上说不在意，心里慌得一批。",
                "ending": "#嘴上说随缘"
            },
            {
                "hook": "不是生活太难。",
                "expand": "是你想得太多。",
                "peak": "做起来，其实没那么难。",
                "ending": "#想太多"
            },
            {
                "hook": "不是你不努力。",
                "expand": "是你方向错了。",
                "peak": "努力在错误的方向，只会越努力越错。",
                "ending": "#方向比努力重要"
            },
            {
                "hook": "其实你怕的不是失败。",
                "expand": "是丢人。",
                "peak": "你怕别人看到你的狼狈。",
                "ending": "#怕丢人"
            },
            {
                "hook": "不是没人懂你。",
                "expand": "是你没给机会。",
                "peak": "你把自己包得太紧。",
                "ending": "#给机会让人懂你"
            },
            {
                "hook": "你不是因为忙。",
                "expand": "你是因为懒。",
                "peak": "忙只是借口，懒才是真相。",
                "ending": "#懒"
            },
            {
                "hook": "不是感情变了。",
                "expand": "是你要求多了。",
                "peak": "一开始你怎么不觉得？",
                "ending": "#要求太多"
            },
            {
                "hook": "不是他不懂浪漫。",
                "expand": "是你没说需要什么。",
                "peak": "别让人猜，直接说。",
                "ending": "#直接说"
            },
            {
                "hook": "其实你不是因为喜欢他。",
                "expand": "你只是害怕孤独。",
                "peak": "孤独比爱可怕，所以你来者不拒。",
                "ending": "#害怕孤独"
            },
            {
                "hook": "不是你没时间。",
                "expand": "你只是不想做。",
                "peak": "把时间留给了更轻松的事。",
                "ending": "#时间都去哪了"
            },
            {
                "hook": "不是生活没意思。",
                "expand": "是你没意思。",
                "peak": "同样的生活，有人过得精彩。",
                "ending": "#让自己有意思"
            },
            {
                "hook": "不是没人愿意懂你。",
                "expand": "是不愿被懂。",
                "peak": "被懂了，就没借口孤独了。",
                "ending": "#不愿被懂"
            },
            {
                "hook": "不是梦想太远。",
                "expand": "是你不敢出发。",
                "peak": "你找了一万个借口，就是不动。",
                "ending": "#不敢出发"
            },
            {
                "hook": "不是世界不公平。",
                "expand": "是你没努力。",
                "peak": "你只看到别人收获，没看到付出。",
                "ending": "#努力"
            },
            {
                "hook": "其实你都知道。",
                "expand": "只是不想做。",
                "peak": "知道和做到，中间隔着十万八千里。",
                "ending": "#知行合一"
            },
            {
                "hook": "不是你不成熟。",
                "expand": "是你不想长大。",
                "peak": "长大太累，所以逃避。",
                "ending": "#不想长大"
            },
            {
                "hook": "不是他不爱了。",
                "expand": "是你不爱了。",
                "peak": "你只是用他的冷漠当借口。",
                "ending": "#其实是你不爱了"
            },
            {
                "hook": "不是圈子小。",
                "expand": "是你不出去。",
                "peak": "宅在家里，圈子当然小。",
                "ending": "#走出去"
            },
            {
                "hook": "不是没优点。",
                "expand": "是你自己不知道。",
                "peak": "你对自己太苛刻。",
                "ending": "#发现自己优点"
            },
        ],
        "open_endings": [
            {
                "hook": "那句话你们都懂。",
                "expand": "就是不敢说。",
                "peak": "——我还没准备好开始",
                "ending": "#你们懂我说的是哪句吗？"
            },
            {
                "hook": "就不用我说了吧。",
                "expand": "你们心里都清楚。",
                "peak": "——有些事大家都懂",
                "ending": "#评论区见"
            },
            {
                "hook": "那句话。",
                "expand": "说出来就不值钱了。",
                "peak": "——你们知道我说的是哪句",
                "ending": "#说不出口的话"
            },
            {
                "hook": "你们都明白的。",
                "expand": "我只是替你说出来。",
                "peak": "——有些话需要有人说",
                "ending": "#终于有人说出来了"
            },
            {
                "hook": "我就不点名了。",
                "expand": "谁疼谁知道。",
                "peak": "——不点名但都知道",
                "ending": "#谁疼谁知道"
            },
            {
                "hook": "有些事。",
                "expand": "心知肚明就好。",
                "peak": "——不需要说破",
                "ending": "#懂的都懂"
            },
            {
                "hook": "你们都懂。",
                "expand": "我就不再重复了。",
                "peak": "——无需多言",
                "ending": "#无需多言"
            },
            {
                "hook": "那句话。",
                "expand": "我们心里都有数。",
                "peak": "——但没人愿意说破",
                "ending": "#心里有数"
            },
            {
                "hook": "我就不说破了。",
                "expand": "给自己留点体面。",
                "peak": "——体面比真相重要",
                "ending": "#给自己留点体面"
            },
            {
                "hook": "你们都知道答案。",
                "expand": "只是不想面对。",
                "peak": "——答案就在那里",
                "ending": "#答案"
            },
            {
                "hook": "我就不提醒了。",
                "expand": "你们自己清楚。",
                "peak": "——不需要提醒",
                "ending": "#你们自己清楚"
            },
            {
                "hook": "有些话说了。",
                "expand": "就没意思了，你们懂。",
                "peak": "——说破就没意思了",
                "ending": "#说破就没意思了"
            },
            {
                "hook": "我们都一样。",
                "expand": "只是没人说破。",
                "peak": "——说出来就不一样了",
                "ending": "#我们都一样"
            },
            {
                "hook": "我就不煽情了。",
                "expand": "你们自己体会。",
                "peak": "——自己体会更深",
                "ending": "#自己体会"
            },
            {
                "hook": "这句话的力量。",
                "expand": "你们感受一下。",
                "peak": "——不需要解释",
                "ending": "#感受一下"
            },
            {
                "hook": "不用我多说。",
                "expand": "你们都懂这种感觉。",
                "peak": "——大家都懂",
                "ending": "#大家都懂"
            },
            {
                "hook": "我就不劝你们了。",
                "expand": "你们自己看着办。",
                "peak": "——自己的选择",
                "ending": "#自己的选择"
            },
            {
                "hook": "这种感受。",
                "expand": "只有经历过的人才懂。",
                "peak": "——经历过才懂",
                "ending": "#经历过才懂"
            },
            {
                "hook": "我就不展开说了。",
                "expand": "你们自己悟。",
                "peak": "——自己悟的才深刻",
                "ending": "#自己悟"
            },
            {
                "hook": "这句话的分量。",
                "expand": "自己体会。",
                "peak": "——不需要解释",
                "ending": "#自己体会"
            },
            {
                "hook": "我就不说透了。",
                "expand": "点到为止。",
                "peak": "——说透就没意思了",
                "ending": "#点到为止"
            },
            {
                "hook": "这种痛。",
                "expand": "只有经历过的人才明白。",
                "peak": "——经历过才明白",
                "ending": "#经历过才明白"
            },
            {
                "hook": "不用我多说。",
                "expand": "看看你自己。",
                "peak": "——答案在自己身上",
                "ending": "#看看你自己"
            },
            {
                "hook": "我就不评价了。",
                "expand": "你们自己判断。",
                "peak": "——自己判断",
                "ending": "#自己判断"
            },
            {
                "hook": "这种心情。",
                "expand": "你们都懂。",
                "peak": "——大家都懂",
                "ending": "#大家都懂"
            },
        ]
    }

    # 评论话术模板（每种钩子类型配3种风格）
    COMMENT_TEMPLATES = {
        "speak_for_me": {
            "discuss": [
                "你们有没有哪句话，一直没说出口？",
                "你最想替自己说什么？",
                "那句没说的话，后来说了吗？"
            ],
            "deepen": [
                "不是不想说，是说了也没人懂。",
                "有些话，说了矫情，不说憋屈。",
                "其实我们都在等一个能听懂的人。"
            ],
            "encourage": [
                "说不出口的话，总有人会懂。",
                "你不需要解释，懂的人自然懂。",
                "总会有人听你说完的。"
            ]
        },
        "resonate_with_me": {
            "discuss": [
                "你们也有过这样的时候吗？",
                "这种感受是不是只有自己懂？",
                "你们是在什么瞬间有这种感觉的？"
            ],
            "deepen": [
                "其实不是孤独，是还没遇到同类。",
                "这种感受，经历过的人自然懂。",
                "一个人扛着，确实很累。"
            ],
            "encourage": [
                "你不是一个人。",
                "总会有人懂你的感受。",
                "一个人也可以好好生活。"
            ]
        },
        "harsh_truths": {
            "discuss": [
                "你们觉得我说得对吗？",
                "这个真相，扎心了吗？",
                "你们还遇到过什么扎心真相？"
            ],
            "deepen": [
                "说白了，就是不敢面对。",
                "有时候真相就是那么残忍。",
                "承认现实，才能改变。"
            ],
            "encourage": [
                "认清真相，依然热爱生活。",
                "直面现实，才能成长。",
                "想通了就好了。"
            ]
        },
        "open_endings": {
            "discuss": [
                "你们懂我说的是哪句吗？",
                "评论区有人能接上吗？",
                "你们心里是不是也有句话？"
            ],
            "deepen": [
                "有些事，大家都懂，只是不说破。",
                "说出来就没意思了。",
                "心知肚明就好。"
            ],
            "encourage": [
                "不用说出来，我们都懂。",
                "给自己留点体面。",
                "有些事不必说透。"
            ]
        }
    }

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._get_default_db_path()
        self._init_db()

    def _get_default_db_path(self) -> str:
        return str(Path(__file__).parent / "database" / "hooks.db")

    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hook_type TEXT NOT NULL,
                hook TEXT NOT NULL,
                expand TEXT NOT NULL,
                peak TEXT NOT NULL,
                ending TEXT NOT NULL,
                full_text TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_full_hook(self, hook_type: str = None) -> Dict:
        """
        获取完整的15秒钩子（包含4个部分）
        
        Returns:
            {
                "type": hook_type,
                "hook": 前3秒,
                "expand": 3-8秒,
                "peak": 8-12秒,
                "ending": 12-15秒,
                "full_text": 完整文案（用换行分隔）
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if hook_type:
            cursor.execute('''
                SELECT id, hook_type, hook, expand, peak, ending FROM hooks
                WHERE hook_type = ?
                ORDER BY RANDOM()
                LIMIT 1
            ''', (hook_type,))
        else:
            cursor.execute('''
                SELECT id, hook_type, hook, expand, peak, ending FROM hooks
                ORDER BY RANDOM()
                LIMIT 1
            ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            full_text = f"{row[2]}\n{row[3]}\n{row[4]}\n{row[5]}"
            return {
                "id": row[0],
                "type": row[1],
                "hook": row[2],
                "expand": row[3],
                "peak": row[4],
                "ending": row[5],
                "full_text": full_text
            }
        return None

    def get_random_hook(self, hook_type: str = None) -> Dict:
        """兼容旧版：获取单句钩子"""
        return self.get_full_hook(hook_type)

    def seed_initial_templates(self):
        """将增强版模板写入数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for hook_type, templates in self.TEMPLATES.items():
            for t in templates:
                full_text = f"{t['hook']}\n{t['expand']}\n{t['peak']}\n{t['ending']}"
                cursor.execute('''
                    INSERT INTO hooks (hook_type, hook, expand, peak, ending, full_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (hook_type, t['hook'], t['expand'], t['peak'], t['ending'], full_text))
        
        conn.commit()
        conn.close()
        total = sum(len(t) for t in self.TEMPLATES.values())
        print(f"[HookEngine] 已初始化 {total} 条增强版钩子模板")

    def get_all_full_hooks(self, hook_type: str = None, limit: int = 100) -> List[Dict]:
        """获取所有完整钩子"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if hook_type:
            cursor.execute('''
                SELECT id, hook_type, hook, expand, peak, ending, used_count FROM hooks
                WHERE hook_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (hook_type, limit))
        else:
            cursor.execute('''
                SELECT id, hook_type, hook, expand, peak, ending, used_count FROM hooks
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "type": r[1],
                "hook": r[2],
                "expand": r[3],
                "peak": r[4],
                "ending": r[5],
                "used_count": r[6]
            }
            for r in rows
        ]

    def get_text_for_tts(self, hook: Dict) -> str:
        """获取TTS语音文本（不含tag）"""
        # 去除 #tag 部分
        def clean_text(text):
            if text.startswith('#'):
                return text.split()[0]  # 只保留tag名
            return text
        
        parts = [
            clean_text(hook['hook']),
            clean_text(hook['expand']),
            clean_text(hook['peak']),
            clean_text(hook['ending'])
        ]
        return '\n'.join(parts)

    def get_comments(self, hook_type: str) -> Dict[str, str]:
        """
        获取三种类型的评论话术
        
        Returns:
            {
                "discuss": 引发讨论型,
                "deepen": 深化观点型,
                "encourage": 情感连接型
            }
        """
        templates = self.COMMENT_TEMPLATES.get(hook_type, {})
        
        return {
            "discuss": random.choice(templates.get("discuss", ["说点什么吧"])),
            "deepen": random.choice(templates.get("deepen", ["确实如此"])),
            "encourage": random.choice(templates.get("encourage", ["加油"]))
        }

    def get_full_hook_with_comments(self, hook_type: str = None) -> Dict:
        """
        获取完整钩子（含文案+评论话术）
        
        Returns:
            {
                "type": hook_type,
                "hook": ...,
                "expand": ...,
                "peak": ...,
                "ending": ...,
                "comments": {
                    "discuss": ...,
                    "deepen": ...,
                    "encourage": ...
                }
            }
        """
        hook = self.get_full_hook(hook_type)
        if hook:
            hook["comments"] = self.get_comments(hook["type"])
        return hook


# 测试
if __name__ == "__main__":
    engine = HookEngine()
    engine.seed_initial_templates()
    
    # 测试获取完整钩子
    print("="*60)
    print("测试完整15秒钩子结构")
    print("="*60)
    
    for hook_type in ["speak_for_me", "resonate_with_me", "harsh_truths", "open_endings"]:
        hook = engine.get_full_hook(hook_type)
        print(f"\n【{hook_type}】")
        print(f"[0-3s] {hook['hook']}")
        print(f"[3-8s] {hook['expand']}")
        print(f"[8-12s] {hook['peak']}")
        print(f"[12-15s] {hook['ending']}")
        print("-"*40)
