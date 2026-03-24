# 项目关系文档

> 本文档记录所有项目/脚本的关系，更新代码时请同步更新本文档
> 最后更新: 2026-03-24

---

## 目录结构

```
/root/.openclaw/workspace/
├── 📱 核心应用
│   ├── multifunction_app.py        # 🎯 主程序 - 统一入口(8080端口)
│   ├── eth_usdt_swap_monitor.py   # ETH永续合约15分钟K线监控
│   └── xau_usdt_swap_monitor.py   # XAU永续合约15分钟K线监控
│
├── 📊 数据存储
│   ├── volume_spikes_db.py        # SQLite数据库模块(主存储)
│   └── logs/                      # 日志目录(符号链接)
│       ├── eth_swap_monitor.log   # ETH监控日志
│       ├── xau_swap_monitor.log   # XAU监控日志
│       ├── volume_spike_records.log # 放量记录备份
│       └── multifunction_app.log  # Flask应用日志
│
├── 📈 图表系统
│   └── charts_fixed/              # K线图表(ETH/BTC/SOL)
│       ├── index.html             # 图表入口
│       ├── ETH_USDT_kline_fixed.html
│       ├── BTC_USDT_kline_fixed.html
│       └── SOL_USDT_kline_fixed.html
│
├── 🤖 AI参数
│   └── ai-params-viewer/          # 参数查看器
│       ├── index.html            # 参数展示页面
│       ├── memory/ → ../memory/   # 符号链接 - 日常记忆
│       ├── *.md → ../*.md        # 符号链接 - 配置文档
│       └── README.md
│
├── 🔧 策略工具
│   └── backtest_engine.py         # 追涨杀跌策略回测系统
│
├── 👶 kids_album_app              # 儿童相册应用
│   ├── android/                   # Android原生(Kotlin)
│   │   ├── app/src/main/java/com/kidsalbum/
│   │   │   ├── adapter/           # 适配器
│   │   │   ├── model/             # 数据模型
│   │   │   ├── screens/          # 页面
│   │   │   └── ui/                # UI组件
│   │   └── app/src/main/res/     # 资源文件
│   ├── flutter/                   # Flutter跨平台
│   │   └── lib/
│   │       ├── screens/           # 页面
│   │       ├── theme/             # 主题
│   │       └── widgets/           # 组件
│   └── web/                       # Web版本
│       ├── index.html             # 入口页
│       ├── home.html              # 首页
│       ├── login.html             # 登录页
│       ├── register.html          # 注册页
│       ├── photo.html             # 照片页
│       ├── profile.html           # 个人页
│       └── DESIGN.md              # 设计文档
│
│   **功能**: 儿童相册展示、分类(生日/日常/旅行/节日)、照片浏览
│   **技术栈**: Kotlin + Flutter + HTML/CSS/JS
│
├── 🎭 modes                       # 模式系统
│   ├── README.md                  # 模式索引
│   ├── crayfish.md                # 🦞 小龙虾模式(默认)
│   ├── musk.md                    # 🚀 马斯克模式
│   ├── musk-toolkit.md            # 🚀 马斯克思维工具箱
│   └── wenshan.md                 # 🧘 文案禅师模式
│
│   **功能**: AI助手人格切换
│   **触发**: 用户消息中的关键词自动切换模式
│   **集成**: SOUL.md 中的核心组件
│
├── ✍️ story_creator              # 故事创作引擎
│   ├── backend/                   # 后端(FastAPI, 端口8000)
│   │   ├── core/                  # 核心逻辑
│   │   └── main.py               # 主入口
│   ├── frontend/                  # 前端(Vue3 + Vue Router)
│   │   └── index.html             # 主页面
│   ├── docs/
│   │   └── PRD.md                # 产品需求文档
│   └── backend.log               # 后端日志
│
│   **功能**: AI小说创作、角色/框架编辑、LLM内容同步
│   **状态**: 降级运行(简单替换)
│   **访问**: /story_creator
│
├── 📋 文档
│   ├── README.md                  # 根目录主文档
│   └── docs/
│       └── PROJECTS.md           # 本文档 - 详细项目关系
│
└── 🎵 抖音EMO（集成到主入口）
    ├── douyin_emo/                # 抖音视频生成系统
    │   ├── core/
    │   │   └── hook_engine.py     # 100条文案钩子模板
    │   ├── generator/
    │   │   ├── tts_wrapper.py    # Edge TTS语音合成
    │   │   └── video_assembler.py # 视频组装(ASS字幕)
    │   ├── output/
    │   │   ├── audio/            # 音频文件
    │   │   ├── videos/           # 视频文件
    │   │   └── emo_hooks_preview.html # 文案库预览
    │   ├── generate.py           # 一键生成入口
    │   ├── tracking_table.md     # 文件追踪表
    │   └── 抖音共鸣系统视频标准SOP.md # 操作规范
    └── 输出访问:
        ├── /douyin_emo           # 系统介绍页
        ├── /douyin_emo/videos    # 视频列表页
        └── /emo_hooks_preview.html # 文案库预览
```

---

## 依赖关系图

```
                          ┌─────────────────┐
                          │   OKX API       │
                          │ K线/成交额数据  │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │     ETH      │ │     XAU      │ │    Flask     │
           │   监控脚本   │ │   监控脚本   │ │   :8080端口  │
           └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                  │                │                │
                  ▼                ▼                ▼
          ┌──────────────┐ ┌──────────────┐ ┌───────────────────────┐
          │  logs/*.log  │ │  logs/*.log  │ │  抖音EMO系统集成       │
          └──────┬───────┘ └──────┬───────┘ │ /douyin_emo 入口      │
                 │                │         │ /douyin_emo/videos    │
                 └────────────────┼─────────┘ /emo_hooks_preview   │
                                  │                 │
                                  ▼                 ▼
                         ┌─────────────────┐ ┌──────────────┐
                         │ volume_spikes   │ │ douyin_emo/ │
                         │     .db         │ │ output/*    │
                         │   (SQLite)      │ └──────────────┘
                         └────────┬────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │   Flask页面  │        │  统计分析    │        │  抖音EMO    │
  │volume_spikes │        │  get_stats   │        │ 视频生成    │
  └──────────────┘        └──────────────┘        └──────────────┘
```

---

## 端口与访问

| 端口 | 服务 | 路由 | 功能 | 状态 |
|------|------|------|------|------|
| 8080 | Flask | `/` | 统一入口（含抖音EMO卡片） | ✅ 运行中 |
| 8080 | Flask | `/market_monitor` | 永续合约监控 | ✅ 运行中 |
| 8080 | Flask | `/volume_spikes` | 放量记录查看 | ✅ 运行中 |
| 8080 | Flask | `/charts_fixed` | K线图表 | ✅ 运行中 |
| 8080 | Flask | `/ai-params-viewer` | AI参数 | ✅ 运行中 |
| 8080 | Flask | `/douyin_emo` | 抖音EMO系统介绍页 | ✅ 运行中 |
| 8080 | Flask | `/douyin_emo/videos` | 抖音EMO视频列表 | ✅ 运行中 |
| 8080 | Flask | `/emo_hooks_preview.html` | 抖音EMO文案库预览 | ✅ 运行中 |
| 8080 | Flask | `/story_creator` | 故事创作引擎 | ✅ 运行中 |
| 8000 | FastAPI | `/api/*` | 故事创作后端API | ✅ 运行中 |

---

### 新增模块端口说明

| 模块 | 端口 | 说明 |
|------|------|------|
| story_creator | 8000 | FastAPI后端，提供LLM内容生成API |
| story_creator | 8080/story_creator | Vue3前端，通过Flask代理访问 |
| kids_album_app | - | 本地开发，运行在独立目录 |
| modes | - | 无独立服务，集成在OpenClaw主进程 |

---

## 数据流详解

### 1. 监控脚本 → 日志

```
eth_usdt_swap_monitor.py
    │
    ├──→ OKX API (K线数据)
    │       GET /api/v5/market/candles
    │       instId=ETH-USDT-SWAP
    │
    └──→ logs/eth_swap_monitor.log
            格式: [timestamp] [LEVEL] 消息
```

### 2. 监控脚本 → 放量记录

```
eth_usdt_swap_monitor.py
    │
    ├── 检测条件: 成交额 >= 前一K线 × 3倍
    │
    └──→ volume_spikes.db (SQLite)
            │
            └──→ 同时写入 logs/volume_spike_records.log (备份)
```

### 3. Flask应用 → 读取数据

```
multifunction_app.py
    │
    ├── /api/market/data/eth → 解析 logs/eth_swap_monitor.log
    ├── /api/market/data/xau → 解析 logs/xau_swap_monitor.log
    ├── /api/market/volume-spikes → 查询 volume_spikes.db
    │
    └── 静态文件:
        ├── charts_fixed/*.html
        └── ai-params-viewer/*
```

---

## 文件关系清单

### 核心文件（不可删除/移动）

| 文件 | 用途 | 被引用位置 | 依赖 |
|------|------|-----------|------|
| `multifunction_app.py` | Flask主程序（含抖音EMO） | nginx/systemd | 全部 |
| `eth_usdt_swap_monitor.py` | ETH监控 | cron | OKX API, logs |
| `xau_usdt_swap_monitor.py` | XAU监控 | cron | OKX API, logs |
| `volume_spikes_db.py` | SQLite模块 | *_monitor, Flask | 无 |
| `backtest_engine.py` | 回测引擎 | 手动 | volume_spikes.db |
| `charts_fixed/` | 图表目录 | Flask | 无 |
| `ai-params-viewer/` | 参数目录 | Flask | memory/*.md |

### 抖音EMO系统文件

| 文件 | 用途 | 被引用位置 | 依赖 |
|------|------|-----------|------|
| `douyin_emo/core/hook_engine.py` | 100条文案钩子模板 | generate.py | 无 |
| `douyin_emo/generator/tts_wrapper.py` | Edge TTS语音 | generate.py | edge-tts API |
| `douyin_emo/generator/video_assembler.py` | ASS字幕+视频组装 | generate.py | FFmpeg |
| `douyin_emo/generate.py` | 一键生成入口 | 手动 | hook_engine, tts_wrapper, video_assembler |
| `douyin_emo/output/videos/*.mp4` | 生成视频 | Flask | 无 |
| `douyin_emo/output/audio/*.mp3` | 生成音频 | video_assembler.py | 无 |
| `douyin_emo/tracking_table.md` | 文件追踪表 | 手动 | 无 |
| `douyin_emo/抖音共鸣系统视频标准SOP.md` | 操作规范 | 文档 | 无 |

### kids_album_app 儿童相册

| 文件 | 用途 | 被引用位置 | 依赖 |
|------|------|-----------|------|
| `kids_album_app/android/` | Android原生代码 | Android Studio | Gradle, Kotlin |
| `kids_album_app/flutter/` | Flutter跨平台代码 | Flutter | Dart SDK |
| `kids_album_app/web/` | Web版本 | 浏览器 | 无 |
| `kids_album_app/web/home.html` | 首页 | 浏览器 | 无 |
| `kids_album_app/web/DESIGN.md` | 设计文档 | 文档 | 无 |

### modes 模式系统

| 文件 | 用途 | 被引用位置 | 依赖 |
|------|------|-----------|------|
| `modes/crayfish.md` | 小龙虾模式配置 | SOUL.md | 无 |
| `modes/musk.md` | 马斯克模式配置 | SOUL.md | 无 |
| `modes/musk-toolkit.md` | 马斯克思维工具箱 | SOUL.md | 无 |
| `modes/wenshan.md` | 文案禅师模式配置 | SOUL.md | 无 |
| `modes/README.md` | 模式索引 | 文档 | 无 |

### story_creator 故事创作引擎

| 文件 | 用途 | 被引用位置 | 依赖 |
|------|------|-----------|------|
| `story_creator/backend/main.py` | FastAPI后端主入口 | 端口8000 | FastAPI, uvicorn |
| `story_creator/backend/core/` | 核心逻辑 | main.py | 无 |
| `story_creator/frontend/index.html` | Vue3前端 | 浏览器 | Vue3, Vue Router |
| `story_creator/docs/PRD.md` | 产品需求文档 | 文档 | 无 |
| `story_creator/backend.log` | 后端日志 | 自动生成 | 无 |

### 日志文件

| 文件 | 用途 | 大小限制 | 清理策略 |
|------|------|---------|---------|
| `logs/eth_swap_monitor.log` | ETH监控 | 10MB | 自动轮转 |
| `logs/xau_swap_monitor.log` | XAU监控 | 10MB | 自动轮转 |
| `logs/volume_spike_records.log` | 放量备份 | 无 | SQLite优先 |
| `logs/multifunction_app.log` | Flask日志 | 无 | 保留7天 |

### 符号链接（自动同步）

| 链接 | 目标 | 用途 | 同步方式 |
|------|------|------|----------|
| `ai-params-viewer/MEMORY.md` | `../MEMORY.md` | 长期记忆 | 实时 |
| `ai-params-viewer/SOUL.md` | `../SOUL.md` | 灵魂设定 | 实时 |
| `ai-params-viewer/USER.md` | `../USER.md` | 用户信息 | 实时 |
| `ai-params-viewer/memory/` | `../memory/` | 日常记忆 | 实时 |
| `logs/*.log` | `../*.log` | 日志汇总 | 实时 |

---

## 运行状态

```bash
# 检查服务状态
ps aux | grep multifunction_app
ps aux | grep _swap_monitor

# 检查端口监听
netstat -tlnp | grep 8080

# 测试API
curl http://localhost:8080/api/market/status
```

---

## 维护指南

### 添加新功能

1. **创建脚本/文件**
   ```bash
   # 新功能脚本放这里
   /root/.openclaw/workspace/new_feature.py
   ```

2. **更新本文档**
   ```markdown
   ## 核心文件（不可删除/移动）
   | 文件 | 用途 | 被引用位置 | 依赖 |
   |------|------|-----------|------|
   | `new_feature.py` | 新功能说明 | - | xxx |
   ```

3. **更新根目录README和主入口**
   - 若需要主入口展示：`multifunction_app.py` 的 `index()` 函数中添加卡片
   - 添加新路由：`@app.route('/new_feature')` 装饰器

4. **测试功能**
   ```bash
   python3 /root/.openclaw/workspace/new_feature.py
   ```

### 抖音EMO系统维护

#### 生成新视频
```bash
cd /root/.openclaw/workspace/douyin_emo
python3 generate.py --count 3 --hook-type harsh_truths
```

#### 视频生成参数
| 参数 | 值 | 说明 |
|------|-----|------|
| MarginL/MarginR | 80 | 左右边距 |
| MarginV | 800 | 垂直位置 |
| 自动换行 | 15字/行 | 超长句子自动拆分 |

#### 文档同步规则
| 代码变更 | 必须同步的文档 |
|----------|---------------|
| 新增路由 | docs/PROJECTS.md（端口与访问表格） |
| 新增文件 | docs/PROJECTS.md（文件关系清单） |
| 修改参数 | 抖音共鸣系统视频标准SOP.md, tracking_table.md |
| 主入口变更 | docs/PROJECTS.md（目录结构、依赖关系图） |

### 更新文档

```bash
# 编辑文档
vim /root/.openclaw/workspace/docs/PROJECTS.md

# 验证语法
markdownlint /root/.openclaw/workspace/docs/PROJECTS.md
```

---

## 更新日志

| 日期 | 变更 | 操作人 |
|------|------|--------|
| 2026-03-24 | 新增 kids_album_app 儿童相册应用模块 | 小龙虾 |
| 2026-03-24 | 新增 modes 模式系统（小龙虾/马斯克/文案禅师） | 小龙虾 |
| 2026-03-24 | 新增 story_creator 故事创作引擎（v1.4.0） | 小龙虾 |
| 2026-03-08 | 抖音EMO系统集成到主入口 | 小龙虾 |
| 2026-03-08 | 字幕参数调整 MarginL/R=50, MarginV=800 | 小小龙 |
| 2026-03-08 | 添加自动换行规则（18字/行） | 小龙虾 |
| 2026-03-07 | 创建文档体系，添加logs目录 | 小龙虾 |
| 2026-03-06 | 添加放量记录+回测系统 | 小龙虾 |
| 2026-03-05 | 初始监控版本 | 小龙虾 |

---

> ⚠️ **重要**：代码更新后必须同步更新本文档
> - 新增路由 → 更新"端口与访问"表格
> - 新增文件 → 更新"文件关系清单"
> - 主入口变更 → 更新"目录结构"和"依赖关系图"
