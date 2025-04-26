import re
from pipelines.keyboards import action_keyboard

def is_youtube_link(url: str) -> bool:
    youtube_patterns = [r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"]
    return any(re.match(pattern, url) for pattern in youtube_patterns)

async def send_action_menu(update_or_query, context, language: str):
    if hasattr(update_or_query, "edit_message_text"):
        await update_or_query.edit_message_text(
            "🛠 Выберите действие:" if language == "ru" else "🛠 Choose an action:",
            reply_markup=action_keyboard(language)
        )
    elif hasattr(update_or_query, "reply_text"):
        await update_or_query.reply_text(
            "🛠 Выберите действие:" if language == "ru" else "🛠 Choose an action:",
            reply_markup=action_keyboard(language)
        )
    else:
        await context.bot.send_message(
            chat_id=update_or_query.effective_chat.id,
            text="🛠 Выберите действие:" if language == "ru" else "🛠 Choose an action:",
            reply_markup=action_keyboard(language)
        )
