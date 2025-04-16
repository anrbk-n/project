import os
import subprocess
import glob
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        print(f"\r📥 [{percent}] ⏱ {speed} | ETA: {eta}", end='', flush=True)
    elif d['status'] == 'finished':
        print('')

def download_with_progress(url, outtmpl, format_code):
    ydl_opts = {
        'format': format_code,
        'outtmpl': outtmpl,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'noplaylist': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
        except DownloadError:
            return None

def merge_video_audio(video_file, audio_file, output_file="video_final.mp4", use_gpu=True):
    video_codec = "h264_nvenc" if use_gpu else "libx264"
    command = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", video_codec,
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_file
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cleanup_temp_files()
    print(f"✅ Видео сохранено: {output_file}")

def cleanup_temp_files():
    for file in glob.glob("video.*") + glob.glob("audio.*"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error {file}: {e}")
