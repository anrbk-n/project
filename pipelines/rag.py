from huggingface_hub import InferenceClient
import os
from typing import List

TRANSCRIPT_PATH = "transcript_punctuated.txt"

client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    token=os.getenv("token")  # экспортируй в .env
)

def load_transcript() -> str:
    if not os.path.exists(TRANSCRIPT_PATH):
        return ""
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def ask_question(query: str) -> str:
    transcript = load_transcript()
    if not transcript:
        return "⚠️ Транскрипт не найден."

    prompt = (
        "Ты — интеллектуальный ассистент, который отвечает на вопросы строго по стенограмме видео. "
        "Используй только информацию из стенограммы. Не придумывай.\n\n"
        f"Стенограмма:\n{transcript}\n\n"
        f"Вопрос: {query}\n"
        f"Ответ:"
    )

    try:
        return client.text_generation(prompt, max_new_tokens=500, temperature=0.7)
    except Exception as e:
        print(f"❌ Ошибка LLM: {e}")
        return "❌ Ошибка при генерации ответа."

def generate_summary() -> str:
    transcript = load_transcript()
    if not transcript:
        return "⚠️ Транскрипт не найден."

    prompt = (
        "Ты — ассистент, который составляет краткое содержание видео.\n"
        "Сделай сжатый, информативный summary следующей стенограммы на русском языке:\n\n"
        f"{transcript}\n\n"
        "Summary:"
    )

    try:
        return client.text_generation(prompt, max_new_tokens=700, temperature=0.7)
    except Exception as e:
        print(f"❌ Ошибка LLM: {e}")
        return "❌ Ошибка при генерации summary."

def generate_timestamps(transcript: str = None) -> List[str]:
    if transcript is None:
        transcript = load_transcript()
    if not transcript:
        return ["⚠️ Транскрипт не найден."]

    paragraphs = transcript.split("\n")
    timestamps = []
    for i, para in enumerate(paragraphs):
        if para.strip():
            timestamps.append(f"{i*30:02d}:00 — {para.strip()[:100]}...")

    return timestamps
