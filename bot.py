import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import json
import os
import asyncio
import pandas as pd

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

CONFIG_FILE = 'rune_cash_bot_config.json'
LEADS_FILE = 'leads.json'
EXCEL_FILE = 'leads.xlsx'

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

class Funnel(StatesGroup):
    age = State()
    city = State()
    final = State()

def save_lead(data):
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    user_ids = [l['id'] for l in leads]
    if data["id"] not in user_ids:
        leads.append(data)
        with open(LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        df = pd.DataFrame(leads)
        df.to_excel(EXCEL_FILE, index=False)

@dp.message_handler(commands=['start'])
async def start_funnel(message: types.Message):
    await Funnel.age.set()
    await message.answer(config["welcome_text"] + "\n\nСколько тебе лет?")

@dp.message_handler(state=Funnel.age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 120):
        await message.answer("Пожалуйста, введи реальный возраст числом:")
        return
    await state.update_data(age=int(message.text))
    await Funnel.next()
    await message.answer("Из какого ты города?")

@dp.message_handler(state=Funnel.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await Funnel.final.set()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("1️⃣", callback_data="choice_1"),
        types.InlineKeyboardButton("2️⃣", callback_data="choice_2")
    )
    await message.answer("💡 Выбери, что тебе ближе:\n\n1️⃣ Хочешь денег сегодня?\n2️⃣ Хочешь денег всегда и много?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("choice_"), state=Funnel.final)
async def process_choice(callback_query: types.CallbackQuery, state: FSMContext):
    choice = callback_query.data.split("_")[1]
    data = await state.get_data()
    lead = {
        "id": callback_query.from_user.id,
        "age": data["age"],
        "city": data["city"],
        "username": callback_query.from_user.username,
        "choice": choice
    }
    save_lead(lead)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "🔮 Настраиваю твой денежный поток...")
    await asyncio.sleep(2)

    link = config["ref_link_1"] if choice == "1" else config["ref_link_2"]
    button = types.InlineKeyboardMarkup()
    button.add(types.InlineKeyboardButton(config["button_text"], url=link))
    await bot.send_message(callback_query.from_user.id, config["final_text"], reply_markup=button)
    await state.finish()

@dp.message_handler()
async def default_reply(message: types.Message):
    await message.answer(config["intro_text"])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен и слушает...")
    executor.start_polling(dp, skip_updates=True)
