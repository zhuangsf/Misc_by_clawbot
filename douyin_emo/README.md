# 抖音EMO视频生成系统

为抖音起号打造的内容生成系统，专注18-25岁EMO女生群体。

## 项目结构

```
douyin_emo/
├── core/
│   ├── hook_engine.py      # 4种钩子生成器（核心）
│   └── qianfan_client.py   # 千帆LLM客户端
├── generator/
│   ├── tts_wrapper.py      # Edge TTS语音合成
│   ├── bgm_manager.py      # 热门BGM管理
│   └── video_assembler.py  # FFmpeg卡点剪辑
├── output/
│   ├── audio/              # 语音文件
│   └── videos/             # 视频成品
├── music/hot_bgm/          # BGM音乐库
├── database/
│   └── hooks.db            # 钩子数据库
└── generate.py             # 主生成脚本
```

## 使用方式

```bash
cd /root/.openclaw/workspace/douyin_emo

# 生成3条视频
python3 generate.py --count 3

# 生成指定类型视频
python3 generate.py --count 3 --hook-type speak_for_me --emotion emo

# 使用LLM生成新钩子
python3 generate.py --count 3 --use-llm
```

## 视频组装器配置（2026-03-08 更新）

| 参数 | 值 | 说明 |
|------|-----|------|
| MarginL | 80 | 左边距 |
| MarginR | 80 | 右边距 |
| MarginV | 800 | 垂直位置（底部算起） |
| Fontsize | 72 | 字体大小 |
| 自动换行 | 15字 | 超过15字自动换行（原18字） |
| 分辨率 | 1080x1920 | 竖屏9:16 |
| 时长 | 15秒 | 标准EMO视频时长 |

## 4种情感钩子

| 钩子类型 | 触发机制 | 示例 |
|----------|----------|------|
| **替我说** | 说出用户心里话 | "有些话你从来不说，但有人懂" |
| **与我同频** | 描述她的状态 | "凌晨三点，你也在等一个人的消息吗" |
| **扎心真相** | 反常识洞察 | "不是没人追你，是你不要" |
| **留白召唤** | 不说全让她补充 | "那句话你们都懂，就是不敢说" |

## 输出

- 视频文件：`output/videos/*.mp4`
- 语音文件：`output/audio/*.mp3`
- 生成清单：`output/manifest.json`

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-03-07 | 初始版本，抖音EMO视频生成系统 |
| v2.0.1 | 2026-03-08 | 更新Margin=80，换行=15字 |
