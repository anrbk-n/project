import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.together.xyz/v1"
)

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.1"
TRANSCRIPT_PATH = "transcript_punctuated.txt"

def load_transcript() -> str:
    if not os.path.exists(TRANSCRIPT_PATH):
        return ""
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def ask_question(query: str) -> str:
    transcript = load_transcript()
    if not transcript:
        return "Транскрипт не найден."

    prompt = (
        "Ты — интеллектуальный ассистент, который отвечает на вопросы строго по стенограмме видео. "
        "Используй только информацию из стенограммы. Не придумывай.\n\n"
        f"Стенограмма:\n{transcript}\n\n"
        f"Вопрос: {query}\n"
        f"Ответ:"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка Together API: {e}")
        return "Ошибка при генерации ответа от модели."


def generate_summary() -> str:
    transcript = load_transcript()
    if not transcript:
        return "Транскрипт не найден."

    prompt = (
        "Ты — интеллектуальный ассистент. Проанализируй стенограмму видео и составь краткое, логичное и информативное summary на русском языке. "
        "Не пересказывай всё дословно. Сконцентрируйся на ключевых идеях, важных терминах и выводах. Используй простой, но деловой стиль изложения.\n\n"
        f"Стенограмма:\n{transcript}\n\n"
        "Summary:"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка Together API: {e}")
        return "Ошибка при генерации summary."


def generate_timestamps(transcript: str = None) -> List[str]:
    if transcript is None:
        transcript = load_transcript()
    if not transcript:
        return ["Транскрипт не найден."]

    paragraphs = transcript.split("\n")
    timestamps = []
    for i, para in enumerate(paragraphs):
        if para.strip():
            timestamps.append(f"{i*30:02d}:00 — {para.strip()[:100]}...")

    return timestamps


def generate_structured_subtitles(transcript: str = None) -> str:
    if transcript is None:
        transcript = load_transcript()
    if not transcript:
        return "Транскрипт не найден."

    prompt = (
        "Раздели следующую стенограмму видео на смысловые блоки. Для каждого блока:\n"
        "- Придумай заголовок\n"
        "- Придумай примерный таймкод (можно использовать 00:00, 00:30, 01:00 и т.п.)\n"
        "- Приведи 2–3 коротких факта или ключевых идеи в виде маркеров\n\n"
        f"Стенограмма:\n{transcript}\n\n"
        "Сформатируй ответ так:\n"
        "00:00 Заголовок\n"
        "- факт 1\n"
        "- факт 2\n"
        "- факт 3\n\n"
        "Ответ:"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка Together API: {e}")
        return "Ошибка при генерации смысловых субтитров."
