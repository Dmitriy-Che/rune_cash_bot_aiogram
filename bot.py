import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import json
import os
import asyncio
from random import choice
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
    name = State()
    age = State()
    city = State()

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
    await Funnel.name.set()
    await message.answer(config["welcome_text"] + "\n\nКак тебя зовут?")

@dp.message_handler(state=Funnel.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await Funnel.next()
    await message.answer("Сколько тебе лет?")

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
    data = await state.get_data()
    lead = {
        "id": message.from_user.id,
        "name": data["name"],
        "age": data["age"],
        "city": data["city"],
        "username": message.from_user.username
    }
    save_lead(lead)

    for text in config["progress_texts"]:
        await message.answer(text)
        await asyncio.sleep(2)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=config["button_text"], url=config["ref_link"]))
    await message.answer(choice(config["offer_texts"]), reply_markup=keyboard)
    await state.finish()

@dp.message_handler()
async def default_reply(message: types.Message):
    await message.answer(config["intro_text"])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен и слушает...")
    executor.start_polling(dp, skip_updates=True)
