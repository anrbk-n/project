import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- API config ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

TRANSCRIPT_PATH = "transcript_punctuated.txt"

# --- Call Gemini API with a prompt ---
def gemini_generate(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Error generating with Gemini"

# --- Load transcript from file ---
def load_transcript() -> str:
    if not os.path.exists(TRANSCRIPT_PATH):
        return ""
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

# --- Generate a detailed summary for the full transcript ---
def generate_summary(language: str = "ru") -> str:
    transcript = load_transcript()
    if not transcript:
        return "Transcript not found."

    if language == "ru":
        prompt = (
            "Ты — профессиональный ассистент, который анализирует полную стенограмму видео.\n"
            "Создай подробное, связное и аккуратное summary.\n\n"
            "Требования:\n"
            "- Охватывай все важные темы и идеи\n"
            "- Пиши в кратком и структурированном стиле\n"
            "- Без воды и повторов\n"
            "- Длина: 15–25 предложений\n"
            "- Пиши на русском языке\n\n"
            f"Текст стенограммы:\n{transcript}\n\n"
            "Summary:"
        )
    elif language == "en":
        prompt = (
            "You are a professional assistant analyzing a full video transcript.\n"
            "Create a detailed, coherent, and structured summary.\n\n"
            "Requirements:\n"
            "- Cover all important topics and ideas\n"
            "- Write clearly and concisely\n"
            "- Avoid repetitions and unnecessary filler\n"
            "- Length: 15–25 sentences\n"
            "- Write in English\n\n"
            f"Transcript:\n{transcript}\n\n"
            "Summary:"
        )
    else:
        return "Unsupported language."

    return gemini_generate(prompt)


# --- Answer a user question based on the transcript ---
def ask_question(query: str, language: str = "ru") -> str:
    transcript = load_transcript()
    if not transcript:
        return "Transcript not found."

    if language == "ru":
        prompt = (
            "Ты — интеллектуальный ассистент, который отвечает на вопросы строго по стенограмме видео.\n"
            "Только используй факты из текста стенограммы, не придумывай.\n\n"
            f"Стенограмма:\n{transcript}\n\n"
            f"Вопрос: {query}\nОтвет:"
        )
    elif language == "en":
        prompt = (
            "You are an intelligent assistant answering questions strictly based on the provided transcript.\n"
            "Only use facts from the transcript, do not invent anything.\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Question: {query}\nAnswer:"
        )
    else:
        return "Unsupported language."

    return gemini_generate(prompt)
