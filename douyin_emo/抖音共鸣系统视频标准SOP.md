# 抖音共鸣系统视频标准 SOP

> 版本: v1.1  
> 最后更新: 2026-03-08 11:10  
> 适用项目: douyin_emo/

---

## 1. 项目概述

| 项目 | 说明 |
|------|------|
| 目标用户 | 18-25 岁EMO女生 |
| 视频时长 | 15 秒 |
| 内容结构 | Hook → 展开 → 峰值 → 留白 |
| 日更新量 | 1-2 条 |

---

## 2. 文案编号规则

### 2.1 编号范围

| 类型 | 编号范围 | 说明 |
|------|----------|------|
| speak_for_me | 001-025 | 替我说 |
| resonate_with_me | 026-050 | 与我同频 |
| harsh_truths | 051-075 | 扎心真相 |
| open_endings | 076-100 | 留白召唤 |

### 2.2 文案文件位置

```
/root/.openclaw/workspace/douyin_emo/core/hook_engine.py
```

### 2.3 追踪表位置

```
/root/.openclaw/workspace/douyin_emo/tracking_table.md
```

---

## 3. 文件命名规则

### 3.1 统一命名格式

| 文件类型 | 命名格式 | 示例 |
|----------|----------|------|
| 音频 | `{编号}.mp3` | `053.mp3` |
| 视频 | `{编号}.mp4` | `053.mp4` |

### 3.2 输出目录

```
/root/.openclaw/workspace/douyin_emo/output/
├── audio/          # 音频文件
│   └── 053.mp3
└── videos/         # 视频文件
    └── 053.mp4
```

---

## 4. 音频生成配置

### 4.1 TTS 设置

| 参数 | 值 | 说明 |
|------|-----|------|
| 引擎 | Edge TTS | 免费中文语音合成 |
| 默认声音 | 晓晓 (zh-CN-XiaoxiaoNeural) | 温柔可爱 |
| 备选声音 | 晓辰 (zh-CN-XiaochenNeural) | 知性御姐 |

### 4.2 符号过滤规则

TTS 文本清理规则（`clean_text_for_tts` 方法）：

| 符号 | 处理方式 |
|------|----------|
| `#` 及之后内容 | **整行删除** |
| `@` 及之后内容 | 整行删除 |
| 其他特殊字符 | 移除 |

**示例：**
```
原文案: "机会来了，你却缩回去了。#你不敢"
TTS文本: "机会来了，你却缩回去了。"
```

### 4.3 音频文件位置

```
/root/.openclaw/workspace/douyin_emo/generator/tts_wrapper.py
```

---

## 5. 视频生成配置

### 5.1 ASS 字幕样式

**文件位置**: `/root/.openclaw/workspace/douyin_emo/generator/video_assembler.py`

**样式参数** (`_create_ass_subtitle` 方法):

| 参数 | 值 | 说明 |
|------|-----|------|
| 字体 | WenQuanYi Zen Hei | 文泉驿正黑，支持中文 |
| 字号 | 72 | 大字体，易读 |
| 粗体 | -1 | 加粗 |
| 对齐方式 | 1 | **左对齐** |
| 边距(MarginL) | 50 | 左边距 |
| 边距(MarginR) | 50 | 右边距 |
| 垂直位置(MarginV) | 800 | 垂直位置 |

**ASS 样式行:**
```
Style: Default,WenQuanYi Zen Hei,72,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,1,50,50,800,1
```

### 5.2 自动换行规则

**重要**：每行最多显示 **18个中文字符**，超过自动从中间拆分换行。

**自动换行逻辑**（`_create_ass_subtitle` 中的 `auto_wrap` 函数）:
- 长句子自动从中间拆分换行
- 确保每行不超过18字
- 避免右侧文字被截断

**示例**:
```
原文: "明明知道不会有回复，还是舍不得放下手机。"
换行后: "明明知道不会有回复，\\N还是舍不得放下手机。"
```

### 5.2 视频参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 分辨率 | 1080x1920 | 竖屏 9:16 |
| 时长 | 15 秒 | 标准短视频 |
| 背景 | 纯黑 | color=black |
| 字幕 | ASS 格式 | FFmpeg subtitles filter |

### 5.3 FFmpeg 命令

```bash
ffmpeg -y \
  -i audio.mp3 \
  -f lavfi -i "color=c=black:s=1080x1920:d=15" \
  -filter_complex "[1:v]subtitles=subtitle.ass[v]" \
  -map 0:a -map "[v]" \
  -t 15 \
  -c:v libx264 -c:a aac \
  -preset fast -crf 23 \
  output.mp4
```

---

## 6. 标准操作流程

### 步骤 1: 确定文案编号

根据 `hook_engine.py` 中的 4 种钩子类型，选择对应的编号范围：

```bash
# 示例：选择 harsh_truths 类型的第 3 个模板
# 编号: 053
```

### 步骤 2: 生成音频

```bash
cd /root/.openclaw/workspace/douyin_emo

# 方法 A: 使用 generate.py 脚本
python3 generate.py --count 1 --hook-type harsh_truths

# 方法 B: 手动生成
python3 -c "
from generator.tts_wrapper import TTSManager
tts = TTSManager()
audio = tts.text_to_speech(
    text='完整文案（含 #tag）',
    voice='zh-CN-XiaoxiaoNeural',
    output_filename='053'
)
"
```

### 步骤 3: 生成视频

```bash
cd /root/.openclaw/workspace/douyin_emo

python3 -c "
from generator.video_assembler import VideoAssembler

assembler = VideoAssembler()
video = assembler.create_simple_video(
    text='完整文案（每句换行）',
    audio_path='audio/053.mp3',
    output_filename='053',
    duration=15.0
)
"
```

### 步骤 4: 验证输出

```bash
# 检查文件
ls -la output/audio/053.mp3
ls -la output/videos/053.mp4

# FFprobe 检查
ffprobe -v quiet -print_format json -show_format output/videos/053.mp4
```

### 步骤 5: 更新追踪表

编辑 `tracking_table.md`，添加新记录：

```markdown
| 053 | 说白了。你不是没机会...#你不敢 | harsh_truths | 053.mp3 | 053.mp4 | ✅ 完成 |
```

---

## 7. 常见问题

### Q1: TTS 读出 "#" 符号？

**原因**: 旧音频文件未应用符号过滤  
**解决**: 重新生成音频，新文件会过滤 # 符号

### Q2: 字幕右侧显示不全？

**原因**: 初始边距 MarginL/MarginR=100，导致显示宽度不足  
**解决**: 
- 调整 MarginL/MarginR 为 50（平衡左右边距与显示宽度）
- 自动换行：每行超过18字自动从中间拆分

### Q3: 字幕上下位置不对？

**原因**: MarginV 参数错误  
**解决**: 设置 MarginV=800（字幕位置往上）

### Q4: 字幕右对齐？

**原因**: ASS 样式 Alignment 参数错误  
**解决**: 使用 Alignment=1（左对齐）

### Q5: 视频生成后文件很小（<1KB）？

**原因**: FFmpeg 视频组装过程中断  
**解决**: 
1. 检查 FFmpeg 是否正常
2. 清理残留进程：`pkill -9 -f video_assembler`
3. 重新生成

### Q6: 音频生成失败？

**原因**: edge_tts 连接问题或网络问题  
**解决**: 
1. 检查网络连接
2. 重试生成
3. 使用其他声音

---

## 8. 访问地址

| 服务 | 地址 |
|------|------|
| 视频文件 | `http://120.48.165.67:8080/douyin_emo/videos/053.mp4` |
| 文件目录 | `/root/.openclaw/workspace/douyin_emo/output/videos/` |

---

## 9. 附录

### 9.1 关键文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `generate.py` | 一键生成入口 |
| 钩子引擎 | `core/hook_engine.py` | 100 条文案模板 |
| TTS 管理 | `generator/tts_wrapper.py` | 音频生成 |
| 视频组装 | `generator/video_assembler.py` | 视频组装 |
| 追踪表 | `tracking_table.md` | 文件对应关系 |
| SOP | `抖音共鸣系统视频标准SOP.md` | 本文档 |

### 9.2 命令速查

```bash
# 生成 1 个视频
python3 generate.py --count 1

# 生成 3 个指定类型视频
python3 generate.py --count 3 --hook-type harsh_truths

# 查看所有输出文件
ls -la output/videos/

# 查看音频目录
ls -la output/audio/
```

---

*遵循此 SOP 确保视频生成的标准化和一致性*
