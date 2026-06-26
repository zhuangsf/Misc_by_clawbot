#!/bin/bash
# 抖音EMO视频生成 - 快速执行脚本
# 
# 用法:
#   ./run_gen.sh 003        # 生成单个视频
#   ./run_gen.sh 003 028    # 批量生成

cd /root/.openclaw/workspace/douyin_emo
source venv/bin/activate
python3 gen_video.py "$@"
