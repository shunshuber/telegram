import os
import re
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from urllib.parse import quote_plus
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8265769208:AAH3R9aTPOwMWV5ir5SjIRQMNPzTbaYI18k"  # Ваш токен
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB - максимальный размер файла для Telegram

# Создаем папку для загрузок
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Функции для загрузки видео
async def download_youtube_video(url, quality='best'):
    ydl_opts = {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]' if quality == 'low' else 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            if not os.path.exists(filepath):
                filepath = filepath.rsplit('.', 1)[0] + '.mp4'
            return filepath, info.get('title', 'video')
    except Exception as e:
        logger.error(f"Ошибка загрузки YouTube видео: {e}")
        return None, None

async def download_tiktok_video(url):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            return filepath, info.get('title', 'video')
    except Exception as e:
        logger.error(f"Ошибка загрузки TikTok видео: {e}")
        return None, None

# Функция для поиска музыки
async def search_music(query):
    # Используем YouTube для поиска музыки
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    
    try:
        response = requests.get(search_url)
        video_ids = re.findall(r'watch\?v=(\S{11})', response.text)
        
        if not video_ids:
            return None, None
            
        video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filepath = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
            return filepath, info.get('title', 'audio')
    except Exception as e:
        logger.error(f"Ошибка поиска музыки: {e}")
        return None, None

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для загрузки видео и поиска музыки.\n\n"
        "Отправь мне ссылку на YouTube или TikTok видео, и я скачаю его для тебя.\n"
        "Или отправь название песни или имя исполнителя, и я найду эту музыку для тебя."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Как использовать бота:\n\n"
        "🎥 Для загрузки видео:\n"
        "Просто отправь ссылку на YouTube или TikTok видео\n\n"
        "🎵 Для поиска музыки:\n"
        "Напиши название песни или имя исполнителя\n\n"
        "Примеры:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://www.tiktok.com/@.../video/...\n"
        "• @taylor swift shake it off\n"
        "• #eminem lose yourself"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    # Проверяем, является ли сообщение ссылкой
    if 'youtube.com/' in message_text or 'youtu.be/' in message_text:
        # Это YouTube ссылка
        await update.message.reply_text("🎥 Начинаю загрузку YouTube видео...")
        
        # Предлагаем выбор качества
        keyboard = [
            [
                InlineKeyboardButton("Высокое качество", callback_data=f"youtube_best_{message_text}"),
                InlineKeyboardButton("Низкое качество", callback_data=f"youtube_low_{message_text}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите качество видео:",
            reply_markup=reply_markup
        )
        
    elif 'tiktok.com/' in message_text:
        # Это TikTok ссылка
        await update.message.reply_text("🎵 Начинаю загрузку TikTok видео...")
        filepath, title = await download_tiktok_video(message_text)
        
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            
            if file_size > MAX_FILE_SIZE:
                await update.message.reply_text("❌ Файл слишком большой для отправки через Telegram.")
            else:
                await update.message.reply_video(
                    video=open(filepath, 'rb'),
                    caption=f"🎵 {title if title else 'TikTok видео'}"
                )
                os.remove(filepath)
        else:
            await update.message.reply_text("❌ Не удалось загрузить видео. Проверьте ссылку и попробуйте снова.")
    
    else:
        # Это поисковый запрос для музыки
        await update.message.reply_text("🎵 Ищу музыку...")
        filepath, title = await search_music(message_text)
        
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            
            if file_size > MAX_FILE_SIZE:
                await update.message.reply_text("❌ Файл слишком большой для отправки через Telegram.")
            else:
                await update.message.reply_audio(
                    audio=open(filepath, 'rb'),
                    caption=f"🎵 {title if title else 'Найденная музыка'}"
                )
                os.remove(filepath)
        else:
            await update.message.reply_text("❌ Не удалось найти музыку. Попробуйте другой запрос.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith('youtube_'):
        parts = data.split('_', 2)
        quality = parts[1]
        url = parts[2]
        
        await query.edit_message_text(text=f"🎥 Загружаю YouTube видео ({'высокое' if quality == 'best' else 'низкое'} качество)...")
        
        filepath, title = await download_youtube_video(url, quality)
        
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            
            if file_size > MAX_FILE_SIZE:
                await query.edit_message_text("❌ Файл слишком большой для отправки через Telegram.")
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(filepath, 'rb'),
                    caption=f"🎥 {title if title else 'YouTube видео'}"
                )
                await query.edit_message_text("✅ Видео успешно отправлено!")
                os.remove(filepath)
        else:
            await query.edit_message_text("❌ Не удалось загрузить видео. Проверьте ссылку и попробуйте снова.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка при обработке сообщения: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже.")

def main():
    # Создаем приложение и передаем ему токен бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()