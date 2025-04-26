import os
import glob
import subprocess
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# --- Download video with a progress bar (for full pipeline) ---
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        print(f"\r📥 [{percent}] ⏱ {speed} | ETA: {eta}", end='', flush=True)
    elif d['status'] == 'finished':
        print('')

def download_with_progress(url, outtmpl, format_code):
    """
    Download video or audio with a progress bar using yt-dlp.
    """
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
            print(f"❌ Download error: {e}")
            return None

# --- Merge video and audio into one mp4 file ---
def merge_video_audio(video_file, audio_file, output_file="download_video.mp4", use_gpu=True):
    """
    Merge separate video and audio files into a single MP4 file using ffmpeg.
    """
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
        print(f"❌ Merge error:\n{result.stderr}")
    else:
        cleanup_temp_files()

# --- Clean up temporary downloaded files ---
def cleanup_temp_files():
    """
    Delete temporary files like video.* and audio.* after merging.
    """
    for file in glob.glob("video.*") + glob.glob("audio.*"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"⚠️ Could not delete {file}: {e}")

# --- Full pipeline: download best video + audio and merge them ---
def run_pipeline(url):
    """
    Full pipeline: download best available video+audio separately and merge into MP4.
    """
    video_file = download_with_progress(url, 'video.%(ext)s', 'bestvideo[ext=mp4]')
    audio_file = download_with_progress(url, 'audio.%(ext)s', 'bestaudio[ext=m4a]')

    if video_file and audio_file:
        merge_video_audio(video_file, audio_file)
    else:
        print("❌ Failed to download video or audio")

# --- Get available video formats (for user to choose) ---
def get_available_formats(url: str):
    """
    Return available video formats (with resolution and size) for selection.
    """
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for fmt in info.get('formats', []):
            if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') != 'none':
                formats.append({
                    'format_id': fmt['format_id'],
                    'resolution': fmt.get('format_note') or f"{fmt.get('height', '?')}p",
                    'filesize': fmt.get('filesize') or 0
                })
        return formats

# --- Download video by chosen format ID (for Telegram bot) ---
def download_video_by_format(url: str, format_id: str, output_path="downloaded_video.mp4"):
    """
    Download the specific video format chosen by the user.
    """
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
