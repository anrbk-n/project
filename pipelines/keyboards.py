from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])

def action_keyboard(language: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Скачать видео" if language == "ru" else "📥 Download video", callback_data="download_video")],
        [InlineKeyboardButton("📝 Получить Summary" if language == "ru" else "📝 Get Summary", callback_data="get_summary")],
        [InlineKeyboardButton("❓ Задать вопрос" if language == "ru" else "❓ Ask a Question", callback_data="ask_question")],
        [InlineKeyboardButton("➕ Прислать новое видео" if language == "ru" else "➕ Send new video link", callback_data="new_video")],
        [InlineKeyboardButton("⬅️ Назад" if language == "ru" else "⬅️ Back", callback_data="go_back")]
    ])

def format_keyboard(formats, language: str):
    buttons = []
    for fmt in formats:
        filesize_text = f" ({fmt['filesize']:.1f} MB)" if fmt['filesize'] else ""
        button_text = f"{fmt['resolution']}{filesize_text}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"format_{fmt['format_id']}")])
    buttons.append([InlineKeyboardButton("⬅️ Назад" if language == "ru" else "⬅️ Back", callback_data="go_back")])
    return InlineKeyboardMarkup(buttons)
