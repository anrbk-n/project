import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
                          filters, ContextTypes, ConversationHandler)
from pipelines.v_download import run_pipeline, get_available_formats, download_video_by_format
from pipelines.subtitles import transcribe_youtube_with_punctuation, save_last_url, load_last_url
from pipelines.rag import generate_summary, ask_question

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

user_sessions = {}

# States
CHOOSING_LANGUAGE, WAITING_LINK, CHOOSING_ACTION, CHOOSING_FORMAT, WAITING_QUESTION = range(5)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.message.reply_text("🌍 Выберите язык общения:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_LANGUAGE

# Handle language choice
async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    language = "ru" if query.data == "lang_ru" else "en"
    user_sessions[user_id] = {"language": language}

    await query.edit_message_text("✅ Язык выбран. Теперь отправьте ссылку на YouTube-видео для обработки.")
    return WAITING_LINK

# Handle incoming YouTube link
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.effective_user.id

    await update.message.reply_text("🔄 Обрабатываю видео, пожалуйста подождите...")

    save_last_url(url)
    user_sessions[user_id]["url"] = url

    formats = get_available_formats(url)
    user_sessions[user_id]["formats"] = formats

    transcribe_youtube_with_punctuation(url)

    keyboard = [
        [InlineKeyboardButton("📥 Скачать видео", callback_data="download_video")],
        [InlineKeyboardButton("📝 Получить Summary", callback_data="get_summary")],
        [InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")]
    ]
    await update.message.reply_text("✅ Видео обработано! Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_ACTION

# Handle main action choice
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "download_video":
        buttons = []
        formats = user_sessions[user_id].get("formats", [])
        for fmt in formats:
            filesize_mb = fmt['filesize'] / (1024 * 1024) if fmt['filesize'] else 0
            button_text = f"{fmt['resolution']} ({filesize_mb:.1f} MB)"
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"format_{fmt['format_id']}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Выберите качество видео:", reply_markup=reply_markup)
        return CHOOSING_FORMAT

    elif query.data == "get_summary":
        language = user_sessions[user_id].get("language", "ru")
        await query.edit_message_text("📝 Генерирую подробное summary...")
        summary = generate_summary(language=language)
        await query.message.reply_text(f"📄 Ваше Summary:\n\n{summary}")
        return ConversationHandler.END

    elif query.data == "ask_question":
        await query.edit_message_text("✍️ Введите ваш вопрос по видео:")
        return WAITING_QUESTION

# Handle format choice and download
async def handle_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chosen_format_id = query.data.replace("format_", "")

    url = user_sessions[user_id]["url"]

    await query.edit_message_text("🔄 Скачиваю выбранное видео, пожалуйста подождите...")
    download_video_by_format(url, chosen_format_id)

    await context.bot.send_video(
        chat_id=query.message.chat_id,
        video=open("downloaded_video.mp4", "rb")
    )

    return ConversationHandler.END

# Handle incoming question
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = user_sessions[user_id].get("language", "ru")

    user_question = update.message.text
    await update.message.reply_text("🔎 Ищу ответ по стенограмме...")
    answer = ask_question(user_question, language=language)
    await update.message.reply_text(f"Ответ:\n{answer}")

    return ConversationHandler.END

# Setup main bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(handle_language_choice)],
            WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)],
            CHOOSING_ACTION: [CallbackQueryHandler(handle_action)],
            CHOOSING_FORMAT: [CallbackQueryHandler(handle_format)],
            WAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
