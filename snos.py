import sqlite3
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import RetryAfter, MessageNotModified
from aiogram.utils import executor
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonOther
import asyncio
from re import compile as compile_link
from os import listdir

# Telegram и сессии
TOKEN = '8265769208:AAH3R9aTPOwMWV5ir5SjIRQMNPzTbaYI18k'  # Замените на ваш токен бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ID супер админа
SUPER_ADMIN_ID = [ 7848751003 ]

# Путь к сессиям Telethon и данные
path = "n3rz4/sessions/"  # Путь к .session файлам
api_id = '25266150'  # Вставьте ваш api_id
api_hash = 'b15d00920b648d9729d5d2867077e4db'  # Вставьте ваш api_hash

# Конфигурация базы данных
conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, subscription_end DATE)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, level INTEGER)''')
conn.commit()

# Стартовое сообщение
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    username = message.from_user.username
    start_date = datetime.now().strftime('%Y-%m-%d')
    
    # Кнопки для отправки жалоб
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("😳 Как сносить?", callback_data='how_to_demolish'),
        InlineKeyboardButton("😎 Причины для сноса", callback_data='reasons_to_demolish')
    )
    
    await message.answer(
        f"Здравствуйте, {username}!\n\n🤖 Бот стабильно работает. Проверка обновления от {start_date}.\n\n"
        "Воспользуйтесь кнопками для отправки жалоб.", reply_markup=keyboard)

# Обработчик нажатий на кнопки
@dp.callback_query_handler(lambda c: c.data == 'how_to_demolish' or c.data == 'reasons_to_demolish')
async def process_callback_button(callback_query: types.CallbackQuery):
    data = callback_query.data
    if data == 'how_to_demolish':
        with open('helpsnos.txt', 'r', encoding='utf-8') as file:
            text = file.read()
    elif data == 'reasons_to_demolish':
        with open('snoshelp.txt', 'r', encoding='utf-8') as file:
            text = file.read()
    
    await bot.send_message(callback_query.from_user.id, text)

# Проверка подписки
def check_subscription(user_id):
    cursor.execute('SELECT subscription_end FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        subscription_end = datetime.strptime(result[0], '%Y-%m-%d')
        return subscription_end >= datetime.now()
    return False


# Проверка уровня администратора
def check_admin_level(user_id, required_level):
    cursor.execute('SELECT level FROM admins WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        admin_level = result[0]
        return admin_level >= required_level
    return False


# Команда выдачи подписки
@dp.message_handler(commands=['addsub'])
async def add_subscription(message: types.Message):
    if check_admin_level(message.from_user.id, 1):
        args = message.text.split()
        if len(args) == 3:
            user_id = int(args[1])
            days = int(args[2])
            
            # Ограничение подписки для админов 1 уровня
            if check_admin_level(message.from_user.id, 1) and days > 10:
                await message.reply("Вы можете выдавать подписку максимум на 10 дней.")
                return
            
            subscription_end = datetime.now() + timedelta(days=days)
            cursor.execute("INSERT OR REPLACE INTO users (id, subscription_end) VALUES (?, ?)", (user_id, subscription_end.strftime('%Y-%m-%d')))
            conn.commit()
            await message.reply(f"Подписка выдана пользователю {user_id} на {days} дней.")
        else:
            await message.reply("Используйте формат команды: /addsub id количество_дней")
    else:
        await message.reply("У вас нет прав для использования этой команды.")


# Команда выдачи админских прав
@dp.message_handler(commands=['addadmin'])
async def add_admin(message: types.Message):
    if message.from_user.id == SUPER_ADMIN_ID:
        args = message.text.split()
        if len(args) == 3:
            user_id = int(args[1])
            level = int(args[2])
            if level in [1, 2]:
                cursor.execute("INSERT OR REPLACE INTO admins (id, level) VALUES (?, ?)", (user_id, level))
                conn.commit()
                await message.reply(f"Админские права уровня {level} выданы пользователю {user_id}.")
            else:
                await message.reply("Уровень администратора должен быть 1 или 2.")
        else:
            await message.reply("Используйте формат команды: /addadmin id уровень")
    else:
        await message.reply("Эта команда доступна только супер администратору.")

# Команда для отправки жалобы
@dp.message_handler(commands=['ss'])
async def ss_command(message: types.Message):
    if check_subscription(message.from_user.id):
        args = message.text.split()
        if len(args) == 2:
            link = args[1]
            successful_reports, failed_reports = await report_message(link, message)
            await message.reply(f"Жалобы отправлены. Успешные: {successful_reports}, Ошибки: {failed_reports}")
        else:
            await message.reply("Используйте формат команды: /ss ссылка")
    else:
        await message.reply("У вас нет активной подписки.")

# Функция для отправки жалоб с обновлением сообщения о процессе
async def report_message(link: str, response_message: types.Message) -> (int, int):
    successful_reports = 0
    failed_reports = 0
    
    # Регулярное выражение для ссылки на сообщение
    message_link_pattern = compile_link(r'https://t.me/(?P<username_or_chat>.+)/(?P<message_id>\d+)')
    match = message_link_pattern.search(link)
    
    if match:
        chat = match.group("username_or_chat")
        message_id = int(match.group("message_id"))
        sessions = listdir(path)
        sessions = [s for s in sessions if s.endswith(".session")]
        
        # Текущее состояние текста, чтобы избежать ненужного редактирования
        current_text = f"🪬 Жалобы отправляются:\n✟ Всего жалоб отправлено: 0"
        
        # Обрабатываем каждую сессию
        for session in sessions:
            try:
                success = await send_report(session, chat, message_id)
                if success:
                    successful_reports += 1
                else:
                    failed_reports += 1
                
                # Обновляем сообщение только после каждых 5 успешных отправленных жалоб
                if successful_reports % 5 == 0:
                    new_text = f"🪬 Жалобы отправляются:\n✟ Всего жалоб отправлено: {successful_reports}"
                    await safe_edit_message_text(
                        response_message.chat.id, 
                        response_message.message_id,
                        current_text,
                        new_text
                    )
                    current_text = new_text  # Обновляем текущее состояние текста
            except Exception as e:
                logging.warning(f"Ошибка при обработке сессии {session}: {e}")
    return successful_reports, failed_reports

# Функция безопасного редактирования сообщения
async def safe_edit_message_text(chat_id, message_id, current_text, new_text):
    if current_text == new_text:
        logging.info("Сообщение не изменилось, редактирование не требуется.")
        return
    
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_text)
    except RetryAfter as e:
        retry_after = e.timeout
        logging.warning(f"Flood control exceeded. Retry in {retry_after} seconds.")
        await asyncio.sleep(retry_after)
        await safe_edit_message_text(chat_id, message_id, current_text, new_text)
    except MessageNotModified:
        logging.info("Сообщение не было изменено, пропускаем редактирование.")

# Функция отправки жалобы через Telethon
async def send_report(session, chat, message_id):
    client = TelegramClient(f"{path}{session}", api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.disconnect()
        return False

    try:
        entity = await client.get_entity(chat)
        await client(ReportRequest(
            peer=entity,
            id=[message_id],
            reason=InputReportReasonOther(),
            message="Данное сообщение похоже на спам."
        ))
        return True
    except Exception as e:
        logging.warning(f"Ошибка при отправке жалобы сессии {session}: {e}")
        return False
    finally:
        await client.disconnect()

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
