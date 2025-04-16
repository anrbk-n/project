import os
import glob
import re
from yt_dlp import YoutubeDL
from deepmultilingualpunctuation import PunctuationModel


def download_subtitles(url, preferred_langs=('ru', 'en')) -> str | None:
    ydl_opts_probe = {'quiet': True, 'skip_download': True}

    def find_lang_match(lang_dict):
        for pref in preferred_langs:
            for actual in lang_dict.keys():
                if actual.startswith(pref):
                    return actual
        return None

    with YoutubeDL(ydl_opts_probe) as ydl:
        info = ydl.extract_info(url, download=False)
        subs = info.get("subtitles", {})
        auto_subs = info.get("automatic_captions", {})

        lang = find_lang_match(subs)
        is_auto = False
        if not lang:
            lang = find_lang_match(auto_subs)
            is_auto = True

        if lang:
            print(f"📥 Найдены {'авто' if is_auto else 'ручные'} субтитры: {lang}")
            ydl_opts_download = {
                'quiet': True,
                'skip_download': True,
                'writesubtitles': not is_auto,
                'writeautomaticsub': is_auto,
                'subtitleslangs': [lang],
                'outtmpl': f"subtitles.{lang}.%(ext)s"
            }
            with YoutubeDL(ydl_opts_download) as ydl2:
                ydl2.download([url])
            matches = glob.glob(f"subtitles.{lang}*.vtt")
            return matches[0] if matches else None

    return None


def clean_and_deduplicate(vtt_path, output_txt="transcript.txt"):
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []
    last_line = ""

    for line in lines:
        line = line.strip()
        if not line or "-->" in line or line.lower().startswith(("kind", "language", "note", "webvtt")):
            continue

        line = re.sub(r"<[^>]+>", "", line).strip()
        if line == last_line:
            continue

        cleaned_lines.append(line)
        last_line = line

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))

    print(f"✅ Чистый текст без повторов: {output_txt}")
    return output_txt


def postprocess_transcript(input_txt_path: str, output_txt_path: str = "transcript_punctuated.txt") -> str:
    model = PunctuationModel()
    
    with open(input_txt_path, "r", encoding="utf-8") as f:
        text = " ".join(line.strip() for line in f.readlines())

    punctuated = model.restore_punctuation(text)

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(punctuated)

    print(f"🧠 Пунктуация восстановлена: {output_txt_path}")
    return output_txt_path


def transcribe_youtube_with_punctuation(url: str) -> str:
    print(f"🔗 Обработка субтитров для видео: {url}")
    vtt_file = download_subtitles(url)

    if not vtt_file:
        print("❌ Субтитры не найдены.")
        return ""

    txt_clean = clean_and_deduplicate(vtt_file)
    os.remove(vtt_file)
    txt_final = postprocess_transcript(txt_clean)

    return txt_final
