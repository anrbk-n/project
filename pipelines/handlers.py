import os
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from pipelines.v_download import run_pipeline, get_available_formats
from pipelines.subtitles import transcribe_youtube_with_punctuation, save_last_url
from pipelines.rag import generate_summary, ask_question
from pipelines.keyboards import action_keyboard, format_keyboard, language_keyboard
from pipelines.utils import is_youtube_link, send_action_menu

CHOOSING_LANGUAGE, WAITING_LINK, CHOOSING_ACTION, CHOOSING_FORMAT, WAITING_QUESTION = range(5)
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Выберите язык общения:\nChoose the language",
        reply_markup=language_keyboard()
    )
    return CHOOSING_LANGUAGE

async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    language = "ru" if query.data == "lang_ru" else "en"
    user_sessions[user_id] = {"language": language}

    text = "✅ Язык выбран. Теперь отправьте ссылку на YouTube-видео для обработки." if language == "ru" else "✅ Language selected. Now send a YouTube video link for processing."
    await query.edit_message_text(text)
    return WAITING_LINK

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    language = user_sessions[user_id].get("language", "ru")

    if not is_youtube_link(url):
        await update.message.reply_text("⚠️ Пожалуйста, отправьте корректную ссылку на YouTube." if language == "ru" else "⚠️ Please send a valid YouTube link.")
        return WAITING_LINK

    processing_message = await update.message.reply_text("🔄 Обрабатываю видео, пожалуйста подождите..." if language == "ru" else "🔄 Processing video, please wait...")

    try:
        save_last_url(url)
        user_sessions[user_id]["url"] = url

        formats = get_available_formats(url)
        if not formats:
            await processing_message.edit_text("⚠️ Не удалось получить доступные форматы." if language == "ru" else "⚠️ Failed to retrieve available formats.")
            await send_action_menu(update, context, language)
            return CHOOSING_ACTION

        user_sessions[user_id]["formats"] = formats
        await processing_message.edit_text("✅ Видео обработано! Выберите действие ниже." if language == "ru" else "✅ Video processed! Choose an action below.")
        await send_action_menu(update, context, language)
        return CHOOSING_ACTION

    except Exception as e:
        await processing_message.edit_text(f"❌ Ошибка: {e}")
        return CHOOSING_ACTION

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    language = user_sessions[user_id].get("language", "ru")

    if query.data == "download_video":
        formats = user_sessions[user_id].get("formats", [])
        await query.edit_message_text(
            "📥 Выберите качество видео:" if language == "ru" else "📥 Choose video quality:",
            reply_markup=format_keyboard(formats, language)
        )
        return CHOOSING_FORMAT

    elif query.data == "get_summary":
        await query.edit_message_text("📝 Генерирую подробное summary..." if language == "ru" else "📝 Generating detailed summary...")
        summary = generate_summary(language=language)
        await query.message.reply_text(f"📄 {'Ваш обзор' if language == 'ru' else 'Your Summary'}:\n\n{summary}")
        await send_action_menu(query, context, language)
        return CHOOSING_ACTION

    elif query.data == "ask_question":
        await query.edit_message_text("✍️ Введите ваш вопрос по видео:" if language == "ru" else "✍️ Enter your question about the video:")
        return WAITING_QUESTION

    elif query.data == "new_video" or query.data == "go_back":
        try:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )
        except Exception as e:
            print(f"⚠️ Ошибка удаления сообщения: {e}")

        await send_action_menu(query, context, language)
        return CHOOSING_ACTION


async def handle_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chosen_format_id = query.data.replace("format_", "")
    language = user_sessions[user_id].get("language", "ru")
    url = user_sessions[user_id]["url"]

    await query.edit_message_text(
        "🔄 Скачиваю выбранное видео, пожалуйста подождите..." if language == "ru"
        else "🔄 Downloading the selected video, please wait..."
    )

    output_file = run_pipeline(url, chosen_format_id)

    if not output_file or not os.path.exists(output_file):
        await query.message.reply_text("❌ Ошибка при скачивании видео." if language == "ru" else "❌ Error downloading video.")
        await send_action_menu(query, context, language)
        return CHOOSING_ACTION

    try:
        with open(output_file, "rb") as f:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=InputFile(f),
                caption="✅ Видео готово!" if language == "ru" else "✅ Video ready!",
                supports_streaming=True,
                read_timeout=300 # Increase read timeout for large files
            )
    except Exception as e:
        await query.message.reply_text(f"❌ Ошибка отправки видео: {e}")
    finally:
        try:
            os.remove(output_file)
        except Exception:
            pass

    await send_action_menu(query, context, language)
    return CHOOSING_ACTION

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = user_sessions[user_id].get("language", "ru")
    user_text = update.message.text

    await update.message.reply_text("🔎 Ищу ответ..." if language == "ru" else "🔎 Searching for an answer...")
    answer = ask_question(user_text, language=language)
    await update.message.reply_text(f"📄 {'Ответ' if language == 'ru' else 'Answer'}:\n{answer}")
    await send_action_menu(update, context, language)
    return CHOOSING_ACTION
