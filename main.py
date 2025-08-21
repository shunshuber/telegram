import asyncio
import logging
from datetime import datetime
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования

logging.basicConfig(level=logging.INFO)

# Токен бота (получите у @BotFather)

BOT_TOKEN = “8265769208:AAH3R9aTPOwMWV5ir5SjIRQMNPzTbaYI18k”

# API ключи (получите на соответствующих сервисах)

WEATHER_API_KEY = “https://wttr.in/{kanibadam}?format=j1”
NEWS_API_KEY = “https://www.reddit.com/r/worldnews.json”

# Инициализация бота и диспетчера

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для FSM

class WeatherStates(StatesGroup):
waiting_for_city = State()

class NewsStates(StatesGroup):
waiting_for_topic = State()

# Клавиатуры

def get_main_keyboard():
keyboard = InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text=“📈 Криптовалюты”, callback_data=“crypto”),
InlineKeyboardButton(text=“🌤 Погода”, callback_data=“weather”)
],
[
InlineKeyboardButton(text=“📰 Новости”, callback_data=“news”),
InlineKeyboardButton(text=“🎲 Случайное число”, callback_data=“random”)
],
[
InlineKeyboardButton(text=“🕐 Время”, callback_data=“time”),
InlineKeyboardButton(text=“💱 Курсы валют”, callback_data=“exchange”)
],
[
InlineKeyboardButton(text=“🎯 Мотивация”, callback_data=“motivation”),
InlineKeyboardButton(text=“📊 Статистика”, callback_data=“stats”)
]
])
return keyboard

def get_crypto_keyboard():
keyboard = InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text=“₿ Bitcoin”, callback_data=“crypto_bitcoin”),
InlineKeyboardButton(text=“Ξ Ethereum”, callback_data=“crypto_ethereum”)
],
[
InlineKeyboardButton(text=“🔸 BNB”, callback_data=“crypto_binancecoin”),
InlineKeyboardButton(text=“💎 Cardano”, callback_data=“crypto_cardano”)
],
[
InlineKeyboardButton(text=“🌟 Solana”, callback_data=“crypto_solana”),
InlineKeyboardButton(text=“📊 Топ 10”, callback_data=“crypto_top10”)
],
[InlineKeyboardButton(text=“◀️ Назад”, callback_data=“back_to_main”)]
])
return keyboard

# Функции для работы с API

async def get_crypto_price(crypto_id):
“”“Получение цены криптовалюты”””
url = f”https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd&include_24hr_change=true”
try:
async with aiohttp.ClientSession() as session:
async with session.get(url) as response:
data = await response.json()
if crypto_id in data:
price = data[crypto_id][‘usd’]
change_24h = data[crypto_id].get(‘usd_24h_change’, 0)
return price, change_24h
return None, None
except Exception as e:
logging.error(f”Ошибка при получении цены криптовалюты: {e}”)
return None, None

async def get_top_crypto():
“”“Получение топ-10 криптовалют”””
url = “https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1”
try:
async with aiohttp.ClientSession() as session:
async with session.get(url) as response:
data = await response.json()
return data
except Exception as e:
logging.error(f”Ошибка при получении топа криптовалют: {e}”)
return None

async def get_weather(city):
“”“Получение погоды”””
url = f”http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru”
try:
async with aiohttp.ClientSession() as session:
async with session.get(url) as response:
if response.status == 200:
data = await response.json()
return data
return None
except Exception as e:
logging.error(f”Ошибка при получении погоды: {e}”)
return None

async def get_exchange_rates():
“”“Получение курсов валют”””
url = “https://api.exchangerate-api.com/v4/latest/USD”
try:
async with aiohttp.ClientSession() as session:
async with session.get(url) as response:
data = await response.json()
return data
except Exception as e:
logging.error(f”Ошибка при получении курсов валют: {e}”)
return None

async def get_motivation_quote():
“”“Получение мотивационной цитаты”””
url = “https://api.quotable.io/random?tags=motivational”
try:
async with aiohttp.ClientSession() as session:
async with session.get(url) as response:
if response.status == 200:
data = await response.json()
return data.get(‘content’, ‘Верь в себя!’), data.get(‘author’, ‘Неизвестный’)
return “Каждый день — это новая возможность стать лучше!”, “Мудрость веков”
except Exception as e:
logging.error(f”Ошибка при получении цитаты: {e}”)
return “Успех приходит к тем, кто не сдается!”, “Мотивационный бот”

# Хранилище статистики пользователей

user_stats = {}

def update_user_stats(user_id, action):
“”“Обновление статистики пользователя”””
if user_id not in user_stats:
user_stats[user_id] = {}

```
if action not in user_stats[user_id]:
    user_stats[user_id][action] = 0

user_stats[user_id][action] += 1
```

# Обработчики команд

@dp.message(Command(“start”))
async def start_command(message: Message):
user_id = message.from_user.id
update_user_stats(user_id, “start”)

```
welcome_text = f"""
```

👋 Привет, {message.from_user.first_name}!

Я многофункциональный бот, который поможет вам с:

📈 **Криптовалюты** - актуальные курсы
🌤 **Погода** - прогноз по городам
📰 **Новости** - последние события
💱 **Валюты** - курсы обмена
🎯 **Мотивация** - вдохновляющие цитаты
📊 **Статистика** - ваша активность

Выберите нужную функцию:
“””

```
await message.answer(welcome_text, reply_markup=get_main_keyboard())
```

@dp.message(Command(“help”))
async def help_command(message: Message):
help_text = “””
🤖 **Доступные команды:**

/start - Запуск бота
/help - Справка
/crypto - Курсы криптовалют
/weather - Погода
/news - Новости
/time - Текущее время
/random - Случайное число

📱 **Или используйте кнопки для удобной навигации!**
“””
await message.answer(help_text)

# Обработчики callback’ов

@dp.callback_query(F.data == “crypto”)
async def crypto_menu(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “crypto_menu”)

```
await callback.message.edit_text(
    "📈 **Криптовалюты**\n\nВыберите криптовалюту для получения актуального курса:",
    reply_markup=get_crypto_keyboard()
)
```

@dp.callback_query(F.data.startswith(“crypto_”))
async def crypto_price(callback: CallbackQuery):
user_id = callback.from_user.id
crypto = callback.data.replace(“crypto_”, “”)
update_user_stats(user_id, f”crypto_{crypto}”)

```
if crypto == "top10":
    await callback.message.edit_text("🔄 Получаю данные топ-10 криптовалют...")
    
    top_crypto = await get_top_crypto()
    if top_crypto:
        text = "📊 **Топ-10 криптовалют по капитализации:**\n\n"
        for i, coin in enumerate(top_crypto, 1):
            name = coin['name']
            symbol = coin['symbol'].upper()
            price = coin['current_price']
            change = coin['price_change_percentage_24h']
            change_emoji = "📈" if change > 0 else "📉"
            
            text += f"{i}. **{name} ({symbol})**\n"
            text += f"💰 ${price:,.2f}\n"
            text += f"{change_emoji} {change:+.2f}%\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="crypto_top10")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            "❌ Не удалось получить данные о криптовалютах",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
            ])
        )
else:
    await callback.message.edit_text(f"🔄 Получаю курс {crypto}...")
    
    price, change_24h = await get_crypto_price(crypto)
    if price:
        change_emoji = "📈" if change_24h > 0 else "📉"
        crypto_name = crypto.replace("bitcoin", "Bitcoin").replace("ethereum", "Ethereum").replace("binancecoin", "BNB").replace("cardano", "Cardano").replace("solana", "Solana")
        
        text = f"💰 **{crypto_name}**\n\n"
        text += f"💵 Цена: **${price:,.2f}**\n"
        text += f"{change_emoji} 24ч: **{change_24h:+.2f}%**\n"
        text += f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"crypto_{crypto}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            "❌ Не удалось получить курс криптовалюты",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
            ])
        )
```

@dp.callback_query(F.data == “weather”)
async def weather_menu(callback: CallbackQuery, state: FSMContext):
user_id = callback.from_user.id
update_user_stats(user_id, “weather”)

```
await callback.message.edit_text("🌤 **Погода**\n\nВведите название города:")
await state.set_state(WeatherStates.waiting_for_city)
```

@dp.message(WeatherStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
city = message.text
await message.answer(f”🔄 Получаю погоду для города {city}…”)

```
weather_data = await get_weather(city)
if weather_data:
    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    humidity = weather_data['main']['humidity']
    description = weather_data['weather'][0]['description']
    wind_speed = weather_data['wind']['speed']
    
    weather_text = f"🌤 **Погода в {city}**\n\n"
    weather_text += f"🌡 Температура: **{temp}°C**\n"
    weather_text += f"🤔 Ощущается: **{feels_like}°C**\n"
    weather_text += f"💧 Влажность: **{humidity}%**\n"
    weather_text += f"💨 Ветер: **{wind_speed} м/с**\n"
    weather_text += f"☁️ Описание: **{description}**"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой город", callback_data="weather")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    await message.answer(weather_text, reply_markup=keyboard)
else:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="weather")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    await message.answer("❌ Город не найден. Проверьте правильность написания.", reply_markup=keyboard)

await state.clear()
```

@dp.callback_query(F.data == “exchange”)
async def exchange_rates(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “exchange”)

```
await callback.message.edit_text("🔄 Получаю курсы валют...")

rates = await get_exchange_rates()
if rates:
    text = "💱 **Курсы валют к доллару США:**\n\n"
    
    important_currencies = {
        'EUR': '🇪🇺 Евро',
        'GBP': '🇬🇧 Фунт стерлингов',
        'JPY': '🇯🇵 Японская йена',
        'RUB': '🇷🇺 Российский рубль',
        'CNY': '🇨🇳 Китайский юань',
        'CHF': '🇨🇭 Швейцарский франк',
        'CAD': '🇨🇦 Канадский доллар',
        'AUD': '🇦🇺 Австралийский доллар'
    }
    
    for code, name in important_currencies.items():
        if code in rates['rates']:
            rate = rates['rates'][code]
            text += f"{name}: **{rate:.4f}**\n"
    
    text += f"\n🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="exchange")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
else:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="exchange")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("❌ Не удалось получить курсы валют", reply_markup=keyboard)
```

@dp.callback_query(F.data == “time”)
async def current_time(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “time”)

```
now = datetime.now()
time_text = f"🕐 **Текущее время:**\n\n"
time_text += f"📅 Дата: **{now.strftime('%d.%m.%Y')}**\n"
time_text += f"🕐 Время: **{now.strftime('%H:%M:%S')}**\n"
time_text += f"📆 День недели: **{now.strftime('%A')}**"

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔄 Обновить", callback_data="time")],
    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
])

await callback.message.edit_text(time_text, reply_markup=keyboard)
```

@dp.callback_query(F.data == “random”)
async def random_number(callback: CallbackQuery):
import random
user_id = callback.from_user.id
update_user_stats(user_id, “random”)

```
number = random.randint(1, 100)
text = f"🎲 **Случайное число:**\n\n**{number}**\n\n🎯 Диапазон: 1-100"

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎲 Новое число", callback_data="random")],
    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
])

await callback.message.edit_text(text, reply_markup=keyboard)
```

@dp.callback_query(F.data == “motivation”)
async def motivation_quote(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “motivation”)

```
await callback.message.edit_text("🔄 Подбираю мотивационную цитату...")

quote, author = await get_motivation_quote()
text = f"🎯 **Мотивация дня:**\n\n*\"{quote}\"*\n\n— {author}"

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎯 Новая цитата", callback_data="motivation")],
    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
])

await callback.message.edit_text(text, reply_markup=keyboard)
```

@dp.callback_query(F.data == “stats”)
async def user_statistics(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “stats”)

```
if user_id in user_stats:
    stats = user_stats[user_id]
    text = f"📊 **Ваша статистика:**\n\n"
    
    action_names = {
        'start': '🚀 Запуски бота',
        'crypto_menu': '📈 Просмотры крипто-меню',
        'weather': '🌤 Запросы погоды',
        'exchange': '💱 Проверки курсов валют',
        'time': '🕐 Проверки времени',
        'random': '🎲 Генераций случайных чисел',
        'motivation': '🎯 Получений мотивации',
        'stats': '📊 Просмотров статистики'
    }
    
    total_actions = sum(stats.values())
    text += f"**Всего действий:** {total_actions}\n\n"
    
    for action, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        if action in action_names:
            text += f"{action_names[action]}: **{count}**\n"
else:
    text = "📊 **Ваша статистика пока пуста**\n\nИспользуйте функции бота, чтобы накопить статистику!"

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats")],
    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
])

await callback.message.edit_text(text, reply_markup=keyboard)
```

@dp.callback_query(F.data == “back_to_main”)
async def back_to_main(callback: CallbackQuery):
text = “🤖 **Главное меню**\n\nВыберите нужную функцию:”
await callback.message.edit_text(text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == “news”)
async def news_menu(callback: CallbackQuery):
user_id = callback.from_user.id
update_user_stats(user_id, “news”)

```
text = "📰 **Новости**\n\nФункция новостей временно недоступна.\nТребуется API ключ от news-сервиса."

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
])

await callback.message.edit_text(text, reply_markup=keyboard)
```

# Запуск бота

async def main():
try:
print(“🤖 Бот запускается…”)
await dp.start_polling(bot)
except Exception as e:
logging.error(f”Ошибка при запуске бота: {e}”)
finally:
await bot.session.close()

if **name** == “**main**”:
asyncio.run(main())
