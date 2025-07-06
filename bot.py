import logging
from aiogram import Bot, Dispatcher, types, executor
import json
import os
from random import choice

API_TOKEN = os.getenv("API_TOKEN")

# Логирование
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

CONFIG_FILE = 'rune_cash_bot_config.json'
LEADS_FILE = 'leads.json'

# Загрузка конфигурации
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {
        "welcome_text": "Добро пожаловать в ✦ Магию и Деньги ✦\n\n🧿 Подключаю эзотерический источник финансов.\n\n🔮 Жми на кнопку, чтобы активировать 🔁 ритуал процветания.",
        "offer_texts": [
            "💰 Получи доступ к *тайному финансовому инструменту*!",
            "🌀 Новый источник изобилия уже рядом…"
        ],
        "button_text": "✨ Жми для активации ✨",
        "ref_link": "https://clicktvf.com/ELAb"
    }

# Сохраняем лида
def save_lead(user: types.User):
    lead = {"id": user.id, "name": user.full_name, "username": user.username}
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    if not any(l['id'] == lead['id'] for l in leads):
        leads.append(lead)
        with open(LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    save_lead(message.from_user)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=config["button_text"], url=config["ref_link"]))
    await message.answer(config["welcome_text"], reply_markup=keyboard)

# Ответ на любое сообщение
@dp.message_handler()
async def echo_random_offer(message: types.Message):
    text = f"{choice(config['offer_texts'])}\n\n👉 {config['ref_link']}"
    await message.answer(text, parse_mode="Markdown")

# Запуск
if __name__ == '__main__':
    print("🤖 Бот запущен и слушает...")
    executor.start_polling(dp, skip_updates=True)
