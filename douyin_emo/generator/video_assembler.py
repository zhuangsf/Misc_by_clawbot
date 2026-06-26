"""
视频组装器
使用FFmpeg进行卡点剪辑，生成15秒EMO视频
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import json


class VideoAssembler:
    """
    视频组装器
    
    功能：
    - 语音+音乐+字幕 合成15秒视频
    - 卡点剪辑（15秒 = 4个4拍）
    - 支持多种输出格式
    """
    
    def __init__(self, output_dir: str = None, ffmpeg_path: str = "ffmpeg"):
        self.output_dir = Path(output_dir or self._get_default_dir())
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        
        # 检查FFmpeg是否可用
        self._check_ffmpeg()

    def _get_default_dir(self) -> str:
        return str(Path(__file__).parent / ".." / "output" / "videos")

    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[VideoAssembler] 警告: FFmpeg检查失败，返回码: {result.returncode}")
                print("请确保FFmpeg已安装: apt install ffmpeg")
        except FileNotFoundError:
            print("[VideoAssembler] 错误: 未找到FFmpeg")
            print("请安装FFmpeg: apt install ffmpeg")

    def assemble_video(
        self,
        audio_path: str,
        output_filename: str = None,
        duration: float = 15.0,
        resolution: str = "1080x1920",
        subtitle_path: str = None,  # ASS字幕文件路径
        bgm_path: str = None,
        output_format: str = "mp4"
    ) -> str:
        """
        组装视频（支持字幕）
        
        Args:
            audio_path: 语音文件路径
            output_filename: 输出文件名
            duration: 视频时长（秒）
            resolution: 分辨率（默认竖屏9:16）
            subtitle_path: ASS字幕文件路径
            bgm_path: BGM文件路径（可选）
            output_format: 输出格式
            
        Returns:
            生成的视频文件路径
        """
        if not output_filename:
            import hashlib
            import time
            timestamp = int(time.time() * 1000)
            output_filename = f"video_{timestamp}"
        
        output_path = self.output_dir / f"{output_filename}.{output_format}"
        
        print(f"[VideoAssembler] 生成视频: {output_path}")
        print(f"  音频: {audio_path}")
        
        has_subtitle = subtitle_path and os.path.exists(subtitle_path)
        has_bgm = bgm_path and os.path.exists(bgm_path)
        
        # 构建FFmpeg命令
        if has_bgm:
            # 有BGM的情况（简化版，暂不支持BGM+字幕）
            cmd = [
                self.ffmpeg_path, "-y",
                "-stream_loop", "-1", "-i", bgm_path,
                "-i", audio_path,
                "-f", "lavfi",
                "-i", f"color=c=black:s={resolution}:d={duration}",
                "-filter_complex",
                "[2:v]" + ("subtitles=" + subtitle_path if has_subtitle else "null") + "[v];"
                "[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.3[a_out]",
                "-t", str(duration),
                "-map", "[v]", "-map", "[a_out]",
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "fast", "-crf", "23",
                str(output_path)
            ]
        else:
            # 无BGM：颜色背景 + 语音 + 字幕
            if has_subtitle:
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-i", audio_path,
                    "-f", "lavfi", "-i", f"color=c=black:s={resolution}:d={duration}",
                    "-filter_complex", f"[1:v]subtitles={subtitle_path}[v]",
                    "-map", "0:a", "-map", "[v]",
                    "-t", str(duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    "-preset", "fast", "-crf", "23",
                    str(output_path)
                ]
            else:
                # 无字幕：简单拼接
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-f", "lavfi", "-i", f"color=c=black:s={resolution}:d={duration}",
                    "-i", audio_path,
                    "-filter_complex", "[0:v][1:a]concat=n=1:v=1:a=1[outv][outa]",
                    "-map", "[outv]", "-map", "[outa]",
                    "-t", str(duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    "-preset", "fast", "-crf", "23",
                    str(output_path)
                ]
        
        # 执行FFmpeg
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"[VideoAssembler] FFmpeg错误: {result.stderr}")
                raise Exception(f"视频生成失败")
            
            print(f"[VideoAssembler] 完成: {output_path}")
            return str(output_path)
            
        except subprocess.TimeoutExpired:
            raise Exception("视频生成超时（超过2分钟）")

    def create_simple_video(
        self,
        text: str,
        audio_path: str,
        output_filename: str = None,
        duration: float = 15.0,
        resolution: str = "1080x1920",
        bgm_path: str = None
    ) -> str:
        """
        简易视频生成（文字黑底 + 语音 + 字幕）
        
        Args:
            text: 文字内容（用于显示在视频上）
            audio_path: 语音文件
            output_filename: 输出文件名
            duration: 时长
            resolution: 分辨率
            bgm_path: BGM文件（可选）
            
        Returns:
            视频文件路径
        """
        # 生成字幕ASS文件
        subtitle_ass = self._create_ass_subtitle(text, duration)
        
        # 组装视频
        output = self.assemble_video(
            audio_path=audio_path,
            output_filename=output_filename,
            duration=duration,
            resolution=resolution,
            subtitle_path=subtitle_ass,
            bgm_path=bgm_path
        )
        
        # 清理临时字幕文件
        if os.path.exists(subtitle_ass):
            os.remove(subtitle_ass)
        
        return output

    def _create_ass_subtitle(self, text: str, duration: float) -> str:
        """
        创建ASS字幕文件
        
        Args:
            text: 字幕文字
            duration: 持续时间
            
        Returns:
            ASS文件路径
        """
        # 简单ASS头
        # 样式说明：
        # - Fontsize: 72（更大字体）
        # - Bold: -1（加粗）
        # - Alignment: 1（左对齐，底部）
        # - MarginL: 100（左边距，避免贴边）
        # - MarginV: 700（垂直位置，从底部算起往上700像素）
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,WenQuanYi Zen Hei,72,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,1,80,80,800,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # 格式化时间
        start = self._format_time(0)
        end = self._format_time(duration)
        
        # 自动换行处理：每行超过15字则换行
        def auto_wrap(text: str, max_chars: int = 15) -> str:
            """
            长句子自动换行
            
            换行规则：
            1. 优先在符号处换行（，。！？：；）
            2. 如果没有符号，超过max_chars在中间位置换行
            """
            # 符号列表
            symbols = '，。！？：；'
            
            lines = text.split('\n')
            wrapped_lines = []
            
            for line in lines:
                # 计算字符长度（中英文都算1个字符）
                if len(line) <= max_chars:
                    wrapped_lines.append(line)
                else:
                    # 优先：在符号处找最后一个可换行点
                    last_symbol_pos = -1
                    for i, char in enumerate(line):
                        if char in symbols and i < len(line) - 1:  # 符号后还有内容
                            last_symbol_pos = i
                    
                    if last_symbol_pos > 0:
                        # 在符号处换行（符号保留在行尾）
                        wrapped_lines.append(line[:last_symbol_pos + 1])
                        wrapped_lines.append(line[last_symbol_pos + 1:])
                    else:
                        # 没有符号，在中间位置换行
                        mid = len(line) // 2
                        wrapped_lines.append(line[:mid])
                        wrapped_lines.append(line[mid:])
            
            return '\\N'.join(wrapped_lines)
        
        # 添加事件行（自动换行处理）
        text_lines = auto_wrap(text)
        ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text_lines}\n"
        
        # 保存文件
        ass_path = self.output_dir / f"temp_subtitle_{int(duration*1000)}.ass"
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return str(ass_path)

    def _format_time(self, seconds: float) -> str:
        """将秒数转换为ASS时间格式 H:MM:SS.cc"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        import mutagen
        
        try:
            from mutagen.mp4 import MP4
            video = MP4(video_path)
            return {
                "duration": video.info.length,
                "bitrate": video.info.bitrate if hasattr(video.info, 'bitrate') else None,
            }
        except:
            # 备选方案：使用ffprobe
            return self._get_video_info_ffprobe(video_path)

    def _get_video_info_ffprobe(self, video_path: str) -> Dict:
        """使用ffprobe获取视频信息"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            format_info = info.get("format", {})
            video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
            
            return {
                "duration": float(format_info.get("duration", 0)),
                "bitrate": int(format_info.get("bit_rate", 0)),
                "width": int(video_stream.get("width", 0)) if video_stream else None,
                "height": int(video_stream.get("height", 0)) if video_stream else None,
            }
        
        return {}

    def list_output_files(self, pattern: str = "*") -> List[Path]:
        """列出输出目录中的文件"""
        return list(self.output_dir.glob(pattern))


# 测试
if __name__ == "__main__":
    assembler = VideoAssembler()
    
    print("视频组装器就绪")
    print(f"输出目录: {assembler.output_dir}")
    
    # 检查FFmpeg
    try:
        result = subprocess.run([assembler.ffmpeg_path, "-version"], capture_output=True)
        print(f"FFmpeg版本: {result.stdout.split(b'\\n')[0].decode()}")
    except:
        print("警告: FFmpeg未安装")
    
    # 示例：生成测试视频（如果有测试音频）
    print("\n使用示例:")
    print("  assembler.create_simple_video(")
    print("      text='有些话你从来不说，但有人懂。',")
    print("      audio_path='path/to/audio.mp3',")
    print("      bgm_path='path/to/bgm.mp3'")
    print("  )")
