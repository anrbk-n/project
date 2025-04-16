import os
import glob
import subprocess
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
        except DownloadError as e:
            print(f"❌ Ошибка загрузки: {e}")
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
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(result.stderr)
    else:
        cleanup_temp_files()



def cleanup_temp_files():
    for file in glob.glob("video.*") + glob.glob("audio.*"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"⚠️ Не удалось удалить {file}: {e}")


def run_pipeline(url):
    video_file = download_with_progress(url, 'video.%(ext)s', 'bestvideo[ext=mp4]')
    audio_file = download_with_progress(url, 'audio.%(ext)s', 'bestaudio[ext=m4a]')

    if video_file and audio_file:
        merge_video_audio(video_file, audio_file)
    else:
        print("❌ Не удалось скачать видео или аудио")
