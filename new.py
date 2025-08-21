import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from datetime import datetime

# Конфигурация
BOT_TOKEN = "8265769208:AAH3R9aTPOwMWV5ir5SjIRQMNPzTbaYI18k"
TRACKED_COINS = {
    'bitcoin': {'symbol': 'BTC', 'threshold': 2.0},
    'ethereum': {'symbol': 'ETH', 'threshold': 3.0},
    'the-open-network': {'symbol': 'TON', 'threshold': 5.0},
    'binancecoin': {'symbol': 'BNB', 'threshold': 4.0},
    'solana': {'symbol': 'SOL', 'threshold': 6.0},
    'cardano': {'symbol': 'ADA', 'threshold': 5.0},
    'ripple': {'symbol': 'XRP', 'threshold': 4.0},
    'dogecoin': {'symbol': 'DOGE', 'threshold': 8.0}
}

# Глобальные переменные
user_settings = {}
last_updates = {}

class CryptoMonitor:
    def __init__(self):
        self.last_prices = {}
        
    async def get_prices(self, coin_ids=None):
        if not coin_ids:
            coin_ids = list(TRACKED_COINS.keys())
            
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            return None

    async def get_coin_list(self):
        url = 'https://api.coingecko.com/api/v3/coins/list'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None

    async def check_price_changes(self, context: ContextTypes.DEFAULT_TYPE):
        current_prices = await self.get_prices()
        if not current_prices:
            return
            
        for chat_id in user_settings:
            if not user_settings[chat_id].get('active', True):
                continue
                
            for coin_id, data in TRACKED_COINS.items():
                if coin_id not in current_prices:
                    continue
                    
                current_price = current_prices[coin_id]['usd']
                change_24h = current_prices[coin_id].get('usd_24h_change', 0)
                
                if coin_id not in self.last_prices:
                    self.last_prices[coin_id] = current_price
                    continue
                
                threshold = user_settings[chat_id].get('thresholds', {}).get(coin_id, data['threshold'])
                change = ((current_price - self.last_prices[coin_id]) / self.last_prices[coin_id]) * 100
                
                if abs(change) >= threshold:
                    message = (f"🚨 {data['symbol']}: ${current_price:.2f}\n"
                              f"📈 Изменение: {change:+.2f}%\n"
                              f"📊 24ч изменение: {change_24h:+.2f}%")
                    
                    # Проверяем, не отправляли ли мы уже уведомление об этом изменении
                    last_update_key = f"{chat_id}_{coin_id}"
                    if last_update_key not in last_updates or (datetime.now() - last_updates[last_update_key]).seconds > 300:
                        await context.bot.send_message(chat_id=chat_id, text=message)
                        last_updates[last_update_key] = datetime.now()
            
            self.last_prices[coin_id] = current_price

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_settings[chat_id] = {'active': True, 'thresholds': {}}
    
    keyboard = [
        [KeyboardButton("📊 Текущие цены"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("🔔 Вкл/Выкл уведомления"), KeyboardButton("❓ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Добро пожаловать в CryptoMonitorBot!\n\n"
        "Я отслеживаю цены криптовалют и отправляю уведомления при значительных изменениях.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )
    
    # Запускаем мониторинг для этого пользователя
    if 'monitor' not in context.bot_data:
        context.bot_data['monitor'] = CryptoMonitor()
        context.job_queue.run_repeating(
            context.bot_data['monitor'].check_price_changes,
            interval=300,
            first=10
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "📊 Текущие цены":
        prices = await context.bot_data['monitor'].get_prices()
        if not prices:
            await update.message.reply_text("Не удалось получить данные о ценах. Попробуйте позже.")
            return
            
        message = "💱 Текущие цены криптовалют:\n\n"
        for coin_id, data in TRACKED_COINS.items():
            if coin_id in prices:
                price = prices[coin_id]['usd']
                change = prices[coin_id].get('usd_24h_change', 0)
                message += f"{data['symbol']}: ${price:.2f} ({change:+.2f}%)\n"
        
        await update.message.reply_text(message)
    
    elif text == "⚙️ Настройки":
        settings_message = (
            "⚙️ Текущие настройки:\n\n"
            f"Уведомления: {'ВКЛ' if user_settings[chat_id]['active'] else 'ВЫКЛ'}\n\n"
            "Пороги уведомлений:\n"
        )
        
        for coin_id, data in TRACKED_COINS.items():
            threshold = user_settings[chat_id].get('thresholds', {}).get(coin_id, data['threshold'])
            settings_message += f"{data['symbol']}: {threshold}%\n"
            
        settings_message += "\nЧтобы изменить порог, отправьте сообщение в формате: COIN порог\nНапример: BTC 3.5"
        
        await update.message.reply_text(settings_message)
    
    elif text == "🔔 Вкл/Выкл уведомления":
        user_settings[chat_id]['active'] = not user_settings[chat_id]['active']
        status = "включены" if user_settings[chat_id]['active'] else "выключены"
        await update.message.reply_text(f"Уведомления {status}!")
    
    elif text == "❓ Помощь":
        help_text = (
            "🤖 CryptoMonitorBot - помощь\n\n"
            "Я отслеживаю цены криптовалют и отправляю уведомления при значительных изменениях.\n\n"
            "Доступные команды:\n"
            "📊 Текущие цены - показать актуальные цены\n"
            "⚙️ Настройки - показать текущие настройки\n"
            "🔔 Вкл/Выкл уведомления - включить/выключить уведомления\n\n"
            "Чтобы изменить порог уведомлений для конкретной монеты, отправьте сообщение в формате:\n"
            "COIN порог\nНапример: BTC 3.5\n\n"
            "По умолчанию я отслеживаю: " + ", ".join([data['symbol'] for data in TRACKED_COINS.values()])
        )
        await update.message.reply_text(help_text)
    
    else:
        # Попытка изменить порог уведомлений
        parts = text.split()
        if len(parts) == 2:
            coin_symbol, threshold_str = parts
            try:
                threshold = float(threshold_str)
                if threshold <= 0:
                    await update.message.reply_text("Порог должен быть положительным числом!")
                    return
                    
                # Находим монету по символу
                coin_id = None
                for cid, data in TRACKED_COINS.items():
                    if data['symbol'].lower() == coin_symbol.lower():
                        coin_id = cid
                        break
                
                if coin_id:
                    if 'thresholds' not in user_settings[chat_id]:
                        user_settings[chat_id]['thresholds'] = {}
                    user_settings[chat_id]['thresholds'][coin_id] = threshold
                    await update.message.reply_text(f"Порог для {TRACKED_COINS[coin_id]['symbol']} изменен на {threshold}%!")
                else:
                    await update.message.reply_text("Монета не найдена! Используйте символы из списка: " + ", ".join([data['symbol'] for data in TRACKED_COINS.values()]))
            except ValueError:
                await update.message.reply_text("Неверный формат! Используйте: COIN порог (например: BTC 3.5)")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка при обработке сообщения: {context.error}")

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("Бот запущен...")
    app.run_polling()