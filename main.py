import asyncio
import logging
import json
import random
import base64
from datetime import datetime, timedelta
from urllib.parse import quote
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота (получите у @BotFather)
BOT_TOKEN = "8265769208:AAH3R9aTPOwMWV5ir5SjIRQMNPzTbaYI18k"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для FSM
class AppStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_movie = State()
    waiting_for_recipe = State()
    waiting_for_qr_text = State()
    waiting_for_translate_text = State()
    waiting_for_color_hex = State()

# Хранилище данных пользователей
user_data = {}
user_stats = {}
user_favorites = {}

def init_user_data(user_id):
    """Инициализация данных пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            "last_activity": datetime.now(),
            "settings": {"language": "ru", "theme": "light"},
            "streak": 0
        }
    
    if user_id not in user_stats:
        user_stats[user_id] = {}
    
    if user_id not in user_favorites:
        user_favorites[user_id] = {
            "cities": [],
            "movies": [],
            "quotes": [],
            "jokes": []
        }

def update_user_stats(user_id, action):
    """Обновление статистики пользователя"""
    init_user_data(user_id)
    
    if action not in user_stats[user_id]:
        user_stats[user_id][action] = 0
    
    user_stats[user_id][action] += 1
    user_data[user_id]["last_activity"] = datetime.now()

# Главная клавиатура с эмодзи и красивым дизайном
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Криптовалюты", callback_data="crypto"),
            InlineKeyboardButton(text="🌤 Погода", callback_data="weather")
        ],
        [
            InlineKeyboardButton(text="🎬 Фильмы", callback_data="movies"),
            InlineKeyboardButton(text="😂 Развлечения", callback_data="entertainment")
        ],
        [
            InlineKeyboardButton(text="🔧 Утилиты", callback_data="utilities"),
            InlineKeyboardButton(text="🍔 Еда", callback_data="food")
        ],
        [
            InlineKeyboardButton(text="🎨 Творчество", callback_data="creative"),
            InlineKeyboardButton(text="📱 Соцсети", callback_data="social")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ]
    ])
    return keyboard

def get_crypto_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₿ Bitcoin", callback_data="crypto_bitcoin"),
            InlineKeyboardButton(text="Ξ Ethereum", callback_data="crypto_ethereum")
        ],
        [
            InlineKeyboardButton(text="🔸 BNB", callback_data="crypto_binancecoin"),
            InlineKeyboardButton(text="💎 Cardano", callback_data="crypto_cardano")
        ],
        [
            InlineKeyboardButton(text="🌟 Solana", callback_data="crypto_solana"),
            InlineKeyboardButton(text="🚀 Dogecoin", callback_data="crypto_dogecoin")
        ],
        [
            InlineKeyboardButton(text="📊 Топ 15", callback_data="crypto_top15"),
            InlineKeyboardButton(text="📈 Трендинг", callback_data="crypto_trending")
        ],
        [
            InlineKeyboardButton(text="💱 Конвертер", callback_data="crypto_converter"),
            InlineKeyboardButton(text="📰 Новости", callback_data="crypto_news")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_entertainment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😂 Анекдоты", callback_data="jokes"),
            InlineKeyboardButton(text="🐱 Котики", callback_data="cats")
        ],
        [
            InlineKeyboardButton(text="🐶 Собачки", callback_data="dogs"),
            InlineKeyboardButton(text="🎯 Активности", callback_data="activities")
        ],
        [
            InlineKeyboardButton(text="💭 Цитаты", callback_data="quotes"),
            InlineKeyboardButton(text="🎲 Игры", callback_data="games")
        ],
        [
            InlineKeyboardButton(text="🔮 Предсказания", callback_data="predictions"),
            InlineKeyboardButton(text="🎪 Факты", callback_data="facts")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_utilities_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 QR код", callback_data="qr_generator"),
            InlineKeyboardButton(text="🌐 IP инфо", callback_data="ip_info")
        ],
        [
            InlineKeyboardButton(text="🔤 Переводчик", callback_data="translator"),
            InlineKeyboardButton(text="🎨 Цвета", callback_data="colors")
        ],
        [
            InlineKeyboardButton(text="📏 Единицы", callback_data="converter"),
            InlineKeyboardButton(text="🧮 Калькулятор", callback_data="calculator")
        ],
        [
            InlineKeyboardButton(text="📅 Календарь", callback_data="calendar"),
            InlineKeyboardButton(text="⏰ Таймеры", callback_data="timers")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_food_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🍽 Рецепты", callback_data="recipes"),
            InlineKeyboardButton(text="🥗 Здоровое питание", callback_data="healthy_food")
        ],
        [
            InlineKeyboardButton(text="🍕 Случайное блюдо", callback_data="random_meal"),
            InlineKeyboardButton(text="🍷 Коктейли", callback_data="cocktails")
        ],
        [
            InlineKeyboardButton(text="🧁 Десерты", callback_data="desserts"),
            InlineKeyboardButton(text="🌍 Кухни мира", callback_data="world_cuisine")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

# Функции для работы с API
async def make_request(url, params=None, timeout=10):
    """Универсальная функция для HTTP запросов"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        logging.error(f"Ошибка запроса к {url}: {e}")
        return None

async def get_crypto_price(crypto_id):
    """Получение цены криптовалюты из CoinGecko API (бесплатно)"""
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": crypto_id,
        "vs_currencies": "usd,rub",
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    
    data = await make_request(url, params)
    if data and crypto_id in data:
        return data[crypto_id]
    return None

async def get_top_crypto(limit=15):
    """Получение топа криптовалют"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false"
    }
    
    return await make_request(url, params)

async def get_trending_crypto():
    """Получение трендинговых криптовалют"""
    url = "https://api.coingecko.com/api/v3/search/trending"
    return await make_request(url)

async def get_weather_free(city):
    """Получение погоды без API ключа через wttr.in"""
    # Используем несколько источников для надежности
    sources = [
        f"https://wttr.in/{quote(city)}?format=j1",
        f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid=demo"  # demo ключ
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            if "current_condition" in data:  # wttr.in format
                current = data["current_condition"][0]
                return {
                    "name": city,
                    "temp": int(current["temp_C"]),
                    "feels_like": int(current["FeelsLikeC"]),
                    "humidity": int(current["humidity"]),
                    "description": current["weatherDesc"][0]["value"],
                    "wind_speed": round(float(current["windspeedKmph"]) / 3.6, 1)  # Конверт в м/с
                }
            elif "main" in data:  # OpenWeather format
                return {
                    "name": data.get("name", city),
                    "temp": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"]
                }
    
    return None

async def get_joke():
    """Получение анекдота"""
    sources = [
        "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit",
        "https://official-joke-api.appspot.com/random_joke"
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            if "joke" in data:  # Single joke
                return data["joke"]
            elif "setup" in data and "delivery" in data:  # Two-part joke
                return f"{data['setup']}\n\n{data['delivery']}"
            elif "setup" in data and "punchline" in data:  # Alternative format
                return f"{data['setup']}\n\n{data['punchline']}"
    
    # Fallback анекдоты
    fallback_jokes = [
        "Почему программисты любят природу? Потому что там нет багов!",
        "Как назвать кота программиста? Кодер!",
        "Почему у программистов плохая осанка? Потому что они всегда склоняются над кодом!",
        "Что общего между программистом и волшебником? Оба создают что-то из ничего!",
        "Сколько программистов нужно, чтобы поменять лампочку? Ни одного - это аппаратная проблема!"
    ]
    return random.choice(fallback_jokes)

async def get_cat_image():
    """Получение картинки кота"""
    sources = [
        "https://api.thecatapi.com/v1/images/search",
        "https://cataas.com/cat?json=true",
        "https://aws.random.cat/meow"
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("url")
            elif "file" in data:  # random.cat format
                return data["file"]
            elif "url" in data:  # cataas format
                return f"https://cataas.com{data['url']}"
    
    return None

async def get_dog_image():
    """Получение картинки собаки"""
    sources = [
        "https://dog.ceo/api/breeds/image/random",
        "https://random.dog/woof.json"
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            if "message" in data:  # dog.ceo format
                return data["message"]
            elif "url" in data:  # random.dog format
                return data["url"]
    
    return None

async def get_activity():
    """Получение предложения активности"""
    url = "https://www.boredapi.com/api/activity"
    data = await make_request(url)
    
    if data and "activity" in data:
        activity = data["activity"]
        activity_type = data.get("type", "Разное")
        participants = data.get("participants", 1)
        
        # Переводим типы активностей
        type_translations = {
            "education": "🎓 Образование",
            "recreational": "🎮 Отдых",
            "social": "👥 Социальное",
            "diy": "🔨 Своими руками",
            "charity": "❤️ Благотворительность",
            "cooking": "🍳 Готовка",
            "relaxation": "😌 Релаксация",
            "music": "🎵 Музыка",
            "busywork": "💼 Работа"
        }
        
        activity_type_ru = type_translations.get(activity_type.lower(), f"🎯 {activity_type}")
        
        return {
            "activity": activity,
            "type": activity_type_ru,
            "participants": participants
        }
    
    # Fallback активности
    activities = [
        {"activity": "Прочитайте интересную статью в интернете", "type": "🎓 Образование", "participants": 1},
        {"activity": "Позвоните старому другу", "type": "👥 Социальное", "participants": 1},
        {"activity": "Приготовьте что-то новое", "type": "🍳 Готовка", "participants": 1},
        {"activity": "Сделайте зарядку", "type": "💪 Спорт", "participants": 1},
        {"activity": "Послушайте новую музыку", "type": "🎵 Музыка", "participants": 1}
    ]
    return random.choice(activities)

async def get_quote():
    """Получение цитаты"""
    sources = [
        "https://api.quotable.io/random",
        "https://zenquotes.io/api/random"
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            if isinstance(data, list):
                data = data[0]
            
            content = data.get("content", data.get("q", ""))
            author = data.get("author", data.get("a", "Неизвестный"))
            
            if content:
                return {"content": content, "author": author}
    
    # Fallback цитаты
    quotes = [
        {"content": "Жизнь - это то, что происходит, пока ты строишь планы", "author": "Джон Леннон"},
        {"content": "Будьте собой, остальные роли уже заняты", "author": "Оскар Уайльд"},
        {"content": "Невозможное сегодня станет возможным завтра", "author": "Константин Циолковский"},
        {"content": "Единственный способ делать великие дела - любить то, что ты делаешь", "author": "Стив Джобс"}
    ]
    return random.choice(quotes)

async def get_fact():
    """Получение интересного факта"""
    sources = [
        "https://uselessfacts.jsph.pl/random.json?language=en",
        "https://catfact.ninja/fact"
    ]
    
    for url in sources:
        data = await make_request(url)
        if data:
            fact = data.get("text", data.get("fact", ""))
            if fact:
                return fact
    
    # Fallback факты
    facts = [
        "Осьминоги имеют три сердца и синюю кровь",
        "Мед никогда не портится - археологи находили съедобный мед возрастом 3000 лет",
        "Бананы радиоактивны из-за содержания калия-40",
        "Акулы существуют дольше деревьев - более 400 миллионов лет",
        "Человеческий мозг содержит примерно 86 миллиардов нейронов"
    ]
    return random.choice(facts)

async def get_ip_info():
    """Получение информации об IP"""
    url = "https://ipapi.co/json/"
    data = await make_request(url)
    
    if data:
        return {
            "ip": data.get("ip", "Не определен"),
            "city": data.get("city", "Не определен"),
            "region": data.get("region", "Не определен"),
            "country": data.get("country_name", "Не определена"),
            "timezone": data.get("timezone", "Не определен"),
            "isp": data.get("org", "Не определен")
        }
    
    return None

async def get_color_info(hex_color):
    """Получение информации о цвете"""
    # Убираем # если есть
    hex_color = hex_color.replace("#", "")
    
    url = f"https://www.thecolorapi.com/id?hex={hex_color}"
    data = await make_request(url)
    
    if data:
        return {
            "hex": data.get("hex", {}).get("value", f"#{hex_color}"),
            "name": data.get("name", {}).get("value", "Без названия"),
            "rgb": f"RGB({data.get('rgb', {}).get('r', 0)}, {data.get('rgb', {}).get('g', 0)}, {data.get('rgb', {}).get('b', 0)})",
            "hsl": f"HSL({data.get('hsl', {}).get('h', 0)}, {data.get('hsl', {}).get('s', 0)}%, {data.get('hsl', {}).get('l', 0)}%)"
        }
    
    return None

def generate_qr_url(text):
    """Генерация URL для QR кода"""
    encoded_text = quote(text)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_text}"

def get_back_keyboard(callback_data="back_to_main"):
    """Универсальная кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    update_user_stats(user_id, "start")
    
    welcome_text = f"""
🚀 **Добро пожаловать, {message.from_user.first_name}!**

Я суперфункциональный бот с множеством возможностей:

💎 **Криптовалюты** - курсы, новости, трендинг
🌤 **Погода** - прогноз без API ключей
🎬 **Фильмы** - поиск и рекомендации
😂 **Развлечения** - анекдоты, мемы, игры
🔧 **Утилиты** - QR коды, переводчик, конвертеers
🍔 **Еда** - рецепты и кулинарные советы
🎨 **Творчество** - генераторы и инструменты
📱 **Социальное** - интересный контент

✨ **Все бесплатно и без ограничений!**

Выберите категорию:
"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# Обработчики callback'ов для криптовалют
@dp.callback_query(F.data == "crypto")
async def crypto_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "crypto_menu")
    
    text = """
💎 **Криптовалютный центр**

Здесь вы можете:
• 📊 Проверить курсы популярных монет
• 📈 Посмотреть трендинговые криптовалюты  
• 💱 Использовать конвертер валют
• 📰 Читать новости криптомира

Выберите действие:
"""
    
    await callback.message.edit_text(text, reply_markup=get_crypto_keyboard())

@dp.callback_query(F.data.startswith("crypto_"))
async def crypto_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.replace("crypto_", "")
    update_user_stats(user_id, f"crypto_{action}")
    
    if action == "top15":
        await callback.message.edit_text("🔄 **Загружаю топ-15 криптовалют...**")
        
        top_crypto = await get_top_crypto(15)
        if top_crypto:
            text = "📊 **Топ-15 криптовалют по капитализации:**\n\n"
            
            for i, coin in enumerate(top_crypto, 1):
                name = coin["name"]
                symbol = coin["symbol"].upper()
                price = coin["current_price"]
                change = coin["price_change_percentage_24h"] or 0
                market_cap = coin["market_cap"]
                
                # Эмодзи для изменения цены
                if change > 5:
                    change_emoji = "🚀"
                elif change > 0:
                    change_emoji = "📈"
                elif change > -5:
                    change_emoji = "📉"
                else:
                    change_emoji = "🔻"
                
                # Форматируем капитализацию
                if market_cap > 1000000000000:  # трлн
                    cap_str = f"${market_cap/1000000000000:.1f}T"
                elif market_cap > 1000000000:  # млрд
                    cap_str = f"${market_cap/1000000000:.1f}B"
                else:  # млн
                    cap_str = f"${market_cap/1000000:.0f}M"
                
                text += f"**{i}.** {name} ({symbol})\n"
                text += f"💰 ${price:,.4f} {change_emoji} {change:+.1f}%\n"
                text += f"📊 Кап: {cap_str}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="crypto_top15"),
                    InlineKeyboardButton(text="📈 Трендинг", callback_data="crypto_trending")
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(
                "❌ **Не удалось загрузить данные**\n\nПопробуйте позже",
                reply_markup=get_back_keyboard("crypto")
            )
    
    elif action == "trending":
        await callback.message.edit_text("🔥 **Загружаю трендинговые криптовалюты...**")
        
        trending_data = await get_trending_crypto()
        if trending_data and "coins" in trending_data:
            text = "🔥 **Сейчас в тренде:**\n\n"
            
            for i, coin in enumerate(trending_data["coins"][:10], 1):
                coin_data = coin["item"]
                name = coin_data["name"]
                symbol = coin_data["symbol"].upper()
                rank = coin_data.get("market_cap_rank", "?")
                
                text += f"**{i}.** {name} ({symbol})\n"
                text += f"📊 Ранг: #{rank}\n"
                text += f"🔥 Трендинг #{i}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="crypto_trending"),
                    InlineKeyboardButton(text="📊 Топ-15", callback_data="crypto_top15")
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(
                "❌ **Не удалось загрузить трендинговые данные**",
                reply_markup=get_back_keyboard("crypto")
            )
    
    else:
        # Обработка конкретных криптовалют
        await callback.message.edit_text(f"🔄 **Загружаю данные для {action}...**")
        
        crypto_data = await get_crypto_price(action)
        if crypto_data:
            usd_price = crypto_data.get("usd", 0)
            rub_price = crypto_data.get("rub", 0)
            change_24h = crypto_data.get("usd_24h_change", 0)
            market_cap = crypto_data.get("usd_market_cap", 0)
            
            # Определяем название
            names = {
                "bitcoin": "Bitcoin (BTC)",
                "ethereum": "Ethereum (ETH)",
                "binancecoin": "BNB",
                "cardano": "Cardano (ADA)",
                "solana": "Solana (SOL)",
                "dogecoin": "Dogecoin (DOGE)"
            }
            
            crypto_name = names.get(action, action.title())
            
            # Эмодзи для изменения
            if change_24h > 5:
                change_emoji = "🚀"
            elif change_24h > 0:
                change_emoji = "📈"
            elif change_24h > -5:
                change_emoji = "📉"
            else:
                change_emoji = "🔻"
            
            text = f"💰 **{crypto_name}**\n\n"
            text += f"💵 **${usd_price:,.2f}**\n"
            text += f"🇷🇺 **₽{rub_price:,.2f}**\n\n"
            text += f"{change_emoji} **24ч: {change_24h:+.2f}%**\n"
            
            if market_cap > 0:
                if market_cap > 1000000000000:
                    cap_str = f"${market_cap/1000000000000:.1f}T"
                elif market_cap > 1000000000:
                    cap_str = f"${market_cap/1000000000:.1f}B"
                else:
                    cap_str = f"${market_cap/1000000:.0f}M"
                text += f"📊 **Капитализация: {cap_str}**\n"
            
            text += f"\n🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data=f"crypto_{action}"),
                    InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_crypto_{action}")
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(
                f"❌ Не удалось загрузить данные для {action}",
                reply_markup=get_back_keyboard("crypto")
            )

# Обработчики для других разделов
@dp.callback_query(F.data == "weather")
async def weather_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    update_user_stats(user_id, "weather")
    
    await callback.message.edit_text(
        "🌤 **Погода**\n\nВведите название города:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AppStates.waiting_for_city)

@dp.message(AppStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    user_id = message.from_user.id
    city = message.text
    
    await message.answer(f"🌤 Загружаю погоду для {city}...")
    
    weather_data = await get_weather_free(city)
    if weather_data:
        text = f"🌤 **Погода в {weather_data['name']}**\n\n"
        text += f"🌡 Температура: {weather_data['temp']}°C\n"
        text += f"💭 Ощущается как: {weather_data['feels_like']}°C\n"
        text += f"💧 Влажность: {weather_data['humidity']}%\n"
        text += f"🌬 Ветер: {weather_data['wind_speed']} м/с\n"
        text += f"📝 Описание: {weather_data['description']}\n\n"
        text += f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"weather_refresh_{city}"),
                InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_weather_{city}")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ])
        
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(
            "❌ Не удалось получить данные о погоде. Проверьте название города.",
            reply_markup=get_back_keyboard()
        )
    
    await state.clear()

@dp.callback_query(F.data == "entertainment")
async def entertainment_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "entertainment")
    
    text = """
😂 **Развлечения**

Выберите категорию:
• 😂 Анекдоты - случайные шутки
• 🐱 Котики - милые фотографии
• 🐶 Собачки - забавные питомцы
• 🎯 Активности - чем заняться
• 💭 Цитаты - мудрые мысли
• 🎲 Игры - мини-игры
• 🔮 Предсказания - что ждет в будущем
• 🎪 Факты - интересные факты
"""
    await callback.message.edit_text(text, reply_markup=get_entertainment_keyboard())

@dp.callback_query(F.data == "jokes")
async def jokes_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "jokes")
    
    await callback.message.edit_text("😂 Загружаю анекдот...")
    
    joke = await get_joke()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😂 Еще анекдот", callback_data="jokes"),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_joke_{hash(joke)}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
    ])
    
    await callback.message.edit_text(f"😂 **Анекдот:**\n\n{joke}", reply_markup=keyboard)

@dp.callback_query(F.data == "cats")
async def cats_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "cats")
    
    await callback.message.edit_text("🐱 Загружаю котика...")
    
    cat_url = await get_cat_image()
    
    if cat_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(cat_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    photo = BufferedInputFile(image_data, filename="cat.jpg")
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🐱 Еще котик", callback_data="cats"),
                            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_cat_{hash(cat_url)}")
                        ],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
                    ])
                    
                    await callback.message.delete()
                    await callback.message.answer_photo(
                        photo=photo,
                        caption="🐱 **Вот ваш котик!**",
                        reply_markup=keyboard
                    )
                    return
    
    await callback.message.edit_text(
        "❌ Не удалось загрузить котика. Попробуйте еще раз.",
        reply_markup=get_back_keyboard("entertainment")
    )

@dp.callback_query(F.data == "dogs")
async def dogs_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "dogs")
    
    await callback.message.edit_text("🐶 Загружаю собачку...")
    
    dog_url = await get_dog_image()
    
    if dog_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(dog_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    photo = BufferedInputFile(image_data, filename="dog.jpg")
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🐶 Еще собачка", callback_data="dogs"),
                            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_dog_{hash(dog_url)}")
                        ],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
                    ])
                    
                    await callback.message.delete()
                    await callback.message.answer_photo(
                        photo=photo,
                        caption="🐶 **Вот ваша собачка!**",
                        reply_markup=keyboard
                    )
                    return
    
    await callback.message.edit_text(
        "❌ Не удалось загрузить собачку. Попробуйте еще раз.",
        reply_markup=get_back_keyboard("entertainment")
    )

@dp.callback_query(F.data == "activities")
async def activities_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "activities")
    
    await callback.message.edit_text("🎯 Ищу активность...")
    
    activity_data = await get_activity()
    
    text = f"🎯 **{activity_data['type']}**\n\n"
    text += f"{activity_data['activity']}\n\n"
    text += f"👥 Участников: {activity_data['participants']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Другая активность", callback_data="activities"),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_activity_{hash(text)}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "quotes")
async def quotes_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "quotes")
    
    await callback.message.edit_text("💭 Ищу цитату...")
    
    quote_data = await get_quote()
    
    text = f"💭 **Цитата дня**\n\n"
    text += f"_{quote_data['content']}_\n\n"
    text += f"— {quote_data['author']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💭 Еще цитата", callback_data="quotes"),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_quote_{hash(text)}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "facts")
async def facts_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "facts")
    
    await callback.message.edit_text("🎪 Ищу интересный факт...")
    
    fact = await get_fact()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎪 Еще факт", callback_data="facts"),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_fact_{hash(fact)}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="entertainment")]
    ])
    
    await callback.message.edit_text(f"🎪 **Интересный факт:**\n\n{fact}", reply_markup=keyboard)

@dp.callback_query(F.data == "utilities")
async def utilities_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "utilities")
    
    text = """
🔧 **Утилиты**

Выберите инструмент:
• 📱 QR код - генератор QR кодов
• 🌐 IP инфо - информация о вашем IP
• 🔤 Переводчик - перевод текста
• 🎨 Цвета - информация о цветах
• 📏 Единицы - конвертер единиц
• 🧮 Калькулятор - простой калькулятор
• 📅 Календарь - просмотр дат
• ⏰ Таймеры - установка таймеров
"""
    await callback.message.edit_text(text, reply_markup=get_utilities_keyboard())

@dp.callback_query(F.data == "qr_generator")
async def qr_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    update_user_stats(user_id, "qr_generator")
    
    await callback.message.edit_text(
        "📱 **Генератор QR кодов**\n\nВведите текст или URL:",
        reply_markup=get_back_keyboard("utilities")
    )
    await state.set_state(AppStates.waiting_for_qr_text)

@dp.message(AppStates.waiting_for_qr_text)
async def process_qr_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    
    qr_url = generate_qr_url(text)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(qr_url) as response:
            if response.status == 200:
                image_data = await response.read()
                photo = BufferedInputFile(image_data, filename="qrcode.png")
                
                await message.answer_photo(
                    photo=photo,
                    caption=f"📱 QR код для: {text}",
                    reply_markup=get_back_keyboard("utilities")
                )
            else:
                await message.answer(
                    "❌ Не удалось сгенерировать QR код",
                    reply_markup=get_back_keyboard("utilities")
                )
    
    await state.clear()

@dp.callback_query(F.data == "ip_info")
async def ip_info_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "ip_info")
    
    await callback.message.edit_text("🌐 Получаю информацию о вашем IP...")
    
    ip_data = await get_ip_info()
    
    if ip_data:
        text = "🌐 **Информация о вашем IP:**\n\n"
        text += f"📡 IP-адрес: `{ip_data['ip']}`\n"
        text += f"🏙 Город: {ip_data['city']}\n"
        text += f"🏛 Регион: {ip_data['region']}\n"
        text += f"🇷🇺 Страна: {ip_data['country']}\n"
        text += f"⏰ Часовой пояс: {ip_data['timezone']}\n"
        text += f"📶 Провайдер: {ip_data['isp']}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="ip_info")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="utilities")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            "❌ Не удалось получить информацию об IP",
            reply_markup=get_back_keyboard("utilities")
        )

@dp.callback_query(F.data == "colors")
async def colors_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    update_user_stats(user_id, "colors")
    
    await callback.message.edit_text(
        "🎨 **Информация о цвете**\n\nВведите HEX-код цвета (например, #FF5733):",
        reply_markup=get_back_keyboard("utilities")
    )
    await state.set_state(AppStates.waiting_for_color_hex)

@dp.message(AppStates.waiting_for_color_hex)
async def process_color_hex(message: Message, state: FSMContext):
    user_id = message.from_user.id
    hex_color = message.text
    
    # Проверяем формат HEX
    import re
    if not re.match(r'^#?[0-9A-Fa-f]{6}$', hex_color):
        await message.answer(
            "❌ Неверный формат HEX-кода. Используйте формат #FF5733 или FF5733",
            reply_markup=get_back_keyboard("utilities")
        )
        return
    
    await message.answer(f"🎨 Загружаю информацию о цвете {hex_color}...")
    
    color_info = await get_color_info(hex_color)
    
    if color_info:
        # Создаем изображение с этим цветом
        from PIL import Image, ImageDraw
        import io
        
        img = Image.new('RGB', (200, 200), color=hex_color)
        draw = ImageDraw.Draw(img)
        
        # Сохраняем изображение в буфер
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        photo = BufferedInputFile(buf.getvalue(), filename="color.png")
        
        text = f"🎨 **Информация о цвете**\n\n"
        text += f"🎨 Название: {color_info['name']}\n"
        text += f"🔷 HEX: {color_info['hex']}\n"
        text += f"🔶 RGB: {color_info['rgb']}\n"
        text += f"🔷 HSL: {color_info['hsl']}"
        
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=get_back_keyboard("utilities")
        )
    else:
        await message.answer(
            "❌ Не удалось получить информацию о цвете",
            reply_markup=get_back_keyboard("utilities")
        )
    
    await state.clear()

@dp.callback_query(F.data == "food")
async def food_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "food")
    
    text = """
🍔 **Еда и рецепты**

Выберите категорию:
• 🍽 Рецепты - поиск рецептов
• 🥗 Здоровое питание - полезные советы
• 🍕 Случайное блюдо - случайный рецепт
• 🍷 Коктейли - рецепты напитков
• 🧁 Десерты - сладкие рецепты
• 🌍 Кухни мира - международная кухня
"""
    await callback.message.edit_text(text, reply_markup=get_food_keyboard())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "back_to_main")
    
    welcome_text = f"""
🚀 **Главное меню**

Выберите категорию:
"""
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard())

# Обработчики для других разделов (можно добавить позже)
@dp.callback_query(F.data == "movies")
async def movies_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "movies")
    
    await callback.message.edit_text(
        "🎬 **Раздел фильмов в разработке**\n\nСкоро здесь появятся поиск фильмов и рекомендации!",
        reply_markup=get_back_keyboard()
    )

@dp.callback_query(F.data == "social")
async def social_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "social")
    
    await callback.message.edit_text(
        "📱 **Социальные функции в разработке**\n\nСкоро здесь появятся интересные социальные функции!",
        reply_markup=get_back_keyboard()
    )

@dp.callback_query(F.data == "creative")
async def creative_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "creative")
    
    await callback.message.edit_text(
        "🎨 **Творческие функции в разработке**\n\nСкоро здесь появятся генераторы и творческие инструменты!",
        reply_markup=get_back_keyboard()
    )

@dp.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "settings")
    
    init_user_data(user_id)
    
    text = f"""
⚙️ **Настройки**

Текущие настройки:
• 🌐 Язык: {user_data[user_id]['settings']['language']}
• 🎨 Тема: {user_data[user_id]['settings']['theme']}

Выберите опцию для изменения:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌐 Язык", callback_data="set_language"),
            InlineKeyboardButton(text="🎨 Тема", callback_data="set_theme")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    update_user_stats(user_id, "stats")
    
    init_user_data(user_id)
    
    # Подсчитываем общее количество действий
    total_actions = sum(user_stats[user_id].values()) if user_id in user_stats else 0
    
    # Находим самые популярные действия
    top_actions = []
    if user_id in user_stats:
        sorted_actions = sorted(user_stats[user_id].items(), key=lambda x: x[1], reverse=True)
        top_actions = sorted_actions[:5]  # Топ-5 действий
    
    text = f"""
📊 **Статистика использования**

👤 Пользователь: {callback.from_user.first_name}
📅 Последняя активность: {user_data[user_id]['last_activity'].strftime('%Y-%m-%d %H:%M')}
🔥 Дней подряд: {user_data[user_id]['streak']}
📈 Всего действий: {total_actions}

🏆 **Топ действий:**
"""
    
    for i, (action, count) in enumerate(top_actions, 1):
        # Преобразуем идентификаторы действий в читаемые названия
        action_names = {
            "start": "Запуск бота",
            "crypto": "Криптовалюты",
            "weather": "Погода",
            "jokes": "Анекдоты",
            "cats": "Котики",
            "dogs": "Собачки",
            "activities": "Активности",
            "quotes": "Цитаты",
            "facts": "Факты",
            "ip_info": "IP информация",
            "qr_generator": "QR генератор",
            "colors": "Цвета"
        }
        
        action_name = action_names.get(action, action)
        text += f"{i}. {action_name}: {count}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Запуск бота
async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())