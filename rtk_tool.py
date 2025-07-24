import subprocess
import re
import os
import json
from datetime import datetime
from tqdm import tqdm

def extract_frames_with_metadata(video_path, srt_path, output_dir):
    """
    提取视频的每一帧图片，并规范化注入SRT中的元数据到EXIF
    添加进度条显示处理进度
    """
    try:
        print("正在初始化...")
        os.makedirs(output_dir, exist_ok=True)
        
        # 解析SRT文件，带进度显示
        print("正在解析SRT元数据...")
        metadata = parse_srt(srt_path)
        if not metadata:
            raise ValueError("未从SRT文件中提取到有效元数据")
        
        print("正在提取视频帧...")
        frame_pattern = os.path.join(output_dir, "img_%04d.jpg")
        ffmpeg_extract_cmd = [
            "ffmpeg",
            "-i", video_path,
            "-qscale:v", "2",
            "-vsync", "0",
            frame_pattern,
            "-y",
            "-loglevel", "error"  # 减少FFmpeg输出
        ]
        subprocess.run(ffmpeg_extract_cmd, check=True)
        print("正在注入元数据到图片...")
        success_count = 0
        with tqdm(total=len(metadata), desc="处理进度", unit="帧") as pbar:
            for frame_data in metadata:
                frame_num = frame_data["frame"]
                frame_file = os.path.join(output_dir, f"img_{frame_num:04d}.jpg")
                
                if os.path.exists(frame_file):
                    try:
                        inject_exif_metadata(frame_file, frame_data)
                        success_count += 1
                    except Exception as e:
                        print(f"\n警告：帧 {frame_num} 元数据注入失败 - {str(e)}")
                else:
                    print(f"\n警告：未找到对应帧 {frame_num} 的图片")
                
                pbar.update(1)
        
        print(f"\n处理完成！成功处理 {success_count}/{len(metadata)} 帧")
        
    except Exception as e:
        print(f"\n处理失败: {str(e)}")
        raise

def parse_srt(srt_path):
    """
    解析SRT文件，提取完整元数据
    :param srt_path: SRT文件路径
    :return: 元数据列表（字典格式）
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    # 增强版正则匹配，提取所有字段
    pattern = re.compile(
        r"FrameCnt: (\d+).*?DiffTime: (\d+)ms\s+"
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s*"
        r"\[iso: ([\d.]+)\] \[shutter: ([\d/.]+)\] \[fnum: ([\d.]+)\] "
        r"\[ev: ([\d.-]+)\] \[color_md ?: (\w+)\] \[ae_meter_md: (\d+)\] "
        r"\[focal_len: ([\d.]+)\] \[dzoom_ratio: ([\d.]+)\], "
        r"\[latitude: ([\d.-]+)\] \[longitude: ([\d.-]+)\] "
        r"\[rel_alt: ([\d.-]+) abs_alt: ([\d.-]+)\] "
        r"\[gb_yaw: ([\d.-]+) gb_pitch: ([\d.-]+) gb_roll: ([\d.-]+)\]",
        re.DOTALL
    )
    
    metadata = []
    for match in pattern.finditer(srt_content):
        frame_data = {
            "frame": int(match.group(1)),
            "diff_time_ms": int(match.group(2)),
            "timestamp": match.group(3),
            "iso": match.group(4),
            "shutter": match.group(5),
            "fnum": match.group(6),
            "ev": match.group(7),
            "color_mode": match.group(8),
            "ae_meter_mode": match.group(9),
            "focal_length": match.group(10),
            "zoom_ratio": match.group(11),
            "latitude": float(match.group(12)),
            "longitude": float(match.group(13)),
            "rel_alt": float(match.group(14)),
            "abs_alt": float(match.group(15)),
            "yaw": float(match.group(16)),
            "pitch": float(match.group(17)),
            "roll": float(match.group(18))
        }
        metadata.append(frame_data)
    
    return metadata

def inject_exif_metadata(image_path, metadata):
    """
    使用exiftool规范化注入元数据到图片EXIF
    :param image_path: 图片路径
    :param metadata: 元数据字典
    """
    try:
        # 标准化GPS坐标格式
        lat_ref = "North" if metadata["latitude"] >= 0 else "South"
        lon_ref = "East" if metadata["longitude"] >= 0 else "West"
        
        # 构建exiftool命令
        exiftool_cmd = [
            "exiftool",
            "-overwrite_original",
            "-charset", "filename=utf8",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLatitude={abs(metadata['latitude'])}",
            f"-GPSLongitudeRef={lon_ref}",
            f"-GPSLongitude={abs(metadata['longitude'])}",
            f"-GPSAltitude={metadata['rel_alt']}",
            f"-GPSAltitudeRef=0",  # 0=高于海平面
            f"-GPSImgDirection={metadata['yaw']}",
            f"-GPSImgDirectionRef=T",  # T=真北方向
            f"-FocalLength={metadata['focal_length']}",
            f"-ApertureValue={metadata['fnum']}",
            f"-ShutterSpeedValue={metadata['shutter']}",
            f"-ISO={metadata['iso']}",
            f"-DateTimeOriginal={metadata['timestamp'].replace('.', ' ')}",
            f"-UserComment={json.dumps(metadata, ensure_ascii=False)}",
            image_path
        ]
        
        subprocess.run(exiftool_cmd, check=True, capture_output=True, text=True)
        
    except subprocess.CalledProcessError as e:
        print(f"元数据注入失败: {e.stderr}")
        raise

if __name__ == "__main__":
    video_path = "./datasets/DJI_20241217180334_0003_V.MP4"
    srt_path = "./datasets/DJI_20241217180334_0003_V.SRT"
    output_dir = "./datasets/output_frames"
    
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE)
        subprocess.run(["exiftool", "-ver"], check=True, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("错误：请先安装ffmpeg和exiftool")
        exit(1)
    
    print("===== 视频帧元数据注入工具 =====")
    extract_frames_with_metadata(video_path, srt_path, output_dir)
    print("处理已完成！输出目录:", os.path.abspath(output_dir))
