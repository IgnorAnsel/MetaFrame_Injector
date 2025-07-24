# 视频帧元数据注入工具

## 功能概述
本工具自动从视频中提取每一帧图像，并将SRT字幕文件中的元数据（GPS坐标、相机参数等）注入到对应帧的EXIF信息中。

## 功能特性
- 🎞️ 从MP4/MOV等视频中提取高质量帧图像
- 📍 注入GPS坐标（纬度、经度、海拔）
- 📷 保留相机参数（ISO、快门、光圈等）
- 🚁 记录无人机姿态数据（偏航角、俯仰角、横滚角）
- ⏱️ 精确时间戳同步
- 📊 支持进度条显示处理状态

## 系统要求
- Python 3.6+
- FFmpeg
- ExifTool

## 安装依赖
```bash
pip install tqdm
sudo apt install ffmpeg exiftool  # Ubuntu/Debian
brew install ffmpeg exiftool     # macOS
