import os
import glob
import subprocess
import json
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

def progress_hook(d):
    if d['status'] == 'downloading':
        downloaded_bytes = d.get('downloaded_bytes', 0)
        total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 0))

        progress = {
            "downloaded_bytes": downloaded_bytes,
            "total_bytes": total_bytes
        }
        with open("progress.json", "w") as f:
            json.dump(progress, f)

        percent = (downloaded_bytes / total_bytes) * 100 if total_bytes else 0
        print(f"\r📥 {downloaded_bytes/1e6:.2f}MB / {total_bytes/1e6:.2f}MB ({percent:.1f}%)", end='', flush=True)

    elif d['status'] == 'finished':
        print('\n✅ Download finished.')

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
        except DownloadError as e:
            return None

def merge_video_audio(video_file, audio_file, output_file="download_video.mp4", use_gpu=True):
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
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cleanup_temp_files()

def cleanup_temp_files():
    for file in glob.glob("video.*") + glob.glob("audio.*"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")

def run_pipeline(url):
    video_file = download_with_progress(url, 'video.%(ext)s', 'bestvideo[ext=mp4]')
    audio_file = download_with_progress(url, 'audio.%(ext)s', 'bestaudio[ext=m4a]')
    if video_file and audio_file:
        merge_video_audio(video_file, audio_file)
    else:
        print("❌ Failed to download video or audio")
    if os.path.exists("progress.json"):
        os.remove("progress.json")
