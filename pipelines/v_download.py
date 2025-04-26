import os
import glob
import subprocess
import uuid
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# Show progress in terminal
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        print(f"\r📥 [{percent}] ⏱ {speed} | ETA: {eta}", end='', flush=True)
    elif d['status'] == 'finished':
        print('')

# Download single stream with specific format
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
            print(f"❌ Download error: {e}")
            return None

# Merge video and audio into one file
def merge_video_audio(video_file, audio_file, output_file, use_gpu=False):
    command = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_file
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("❌ Merge error:")
        print(result.stderr)
    else:
        print(f"✅ Merge complete: {output_file}")
        cleanup_temp_files()

# Clean up temporary audio/video files
def cleanup_temp_files():
    for file in glob.glob("video.*") + glob.glob("audio.*"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"⚠️ Could not remove {file}: {e}")

# Show available formats for user selection 
def get_available_formats(url: str):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        all_formats = []

        for fmt in info.get("formats", []):
            if (
                fmt.get("vcodec") != "none" and
                fmt.get("ext") == "mp4" and
                fmt.get("height", 0) >= 480
            ):
                filesize = fmt.get("filesize") or fmt.get("filesize_approx")
                size_mb = (filesize / (1024 * 1024)) if filesize else 0

                all_formats.append({
                    "format_id": fmt["format_id"],
                    "resolution": f"{fmt.get('height', '?')}p",
                    "height": fmt.get("height", 0),
                    "filesize": size_mb
                })

        if not all_formats:
            return []

        # --- Группируем по разрешению: оставляем самый лёгкий файл в каждой группе
        best_formats = {}
        for fmt in all_formats:
            res = fmt["height"]  # Например, 480, 720, 1080
            if res not in best_formats:
                best_formats[res] = fmt
            else:
                if fmt["filesize"] and fmt["filesize"] < best_formats[res]["filesize"]:
                    best_formats[res] = fmt

        # Сортируем по разрешению по возрастанию (сначала 480p, потом 720p и т.д.)
        sorted_formats = sorted(best_formats.values(), key=lambda x: x["height"])

        return [
            {
                "format_id": f["format_id"],
                "resolution": f"{f['height']}p",
                "filesize": f["filesize"]
            }
            for f in sorted_formats
        ]


# Download video and audio, then merge
def run_pipeline(url, format_id):
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"downloaded_video_{unique_id}.mp4"

    video_file = download_with_progress(url, "video.%(ext)s", format_id)
    audio_file = download_with_progress(url, "audio.%(ext)s", "bestaudio[ext=m4a]")

    if video_file and audio_file:
        merge_video_audio(video_file, audio_file, output_file=output_filename, use_gpu=False)
        return output_filename
    else:
        print("❌ Не удалось скачать видео или аудио.")
        return None
