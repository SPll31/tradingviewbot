import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from tradingview import TradingViewConnection
from aiohttp import web

API_TOKEN = os.getenv("API_TOKEN")
DATA_FILE = "users.json"
MESSAGES_FILE = "messages.json"
OWNER_ID = [5964376811, 394824718, 1255352761]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
users = {}
messages = {}


async def handle_main_page(request):
    return web.Response(text="RESPONSE 200",
                        content_type="text/html")


async def create_server():
    app = web.Application()

    app.router.add_get("/", handle_main_page)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=os.getenv("PORT") or 10000)
    await site.start()

    return runner


def load_users_from_file():
    global users
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            users = json.load(file)
            users = {int(k): {**v,
                              "connection": TradingViewConnection(
                                  v["currency"], v["timeframe"]["code"])}
                     for k, v in users.items()}


def load_messages_from_file():
    global messages
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r", encoding='utf-8') as file:
            messages = json.load(file)


def save_users_to_file():
    cleaned_users = {
        user_id: {key: value for key, value in user_data.items()
                  if key != "connection"}
        for user_id, user_data in users.items()
    }

    with open(DATA_FILE, "w") as file:
        json.dump(cleaned_users, file, indent=4)


async def send_updates(connection, user):
    async for signal, close in connection.connect_and_send():
        await bot.send_message(user,
                               messages["SIGNAL"].format(
                                   "🔴" if signal == "Short" else "🟢",
                                   signal, close,
                                   users[user]["currency"],
                                   users[user]["timeframe"]["display"]))


timeframes = [
    {"display": "1 минута", "code": "1"},
    {"display": "3 минуты", "code": "3"},
    {"display": "5 минут", "code": "5"},
    {"display": "15 минут", "code": "15"},
    {"display": "30 минут", "code": "30"},
    {"display": "45 минут", "code": "45"},
    {"display": "1 час", "code": "60"},
    {"display": "2 часа", "code": "120"},
    {"display": "3 часа", "code": "180"},
    {"display": "4 часа", "code": "240"},
    {"display": "1 день", "code": "1D"},
    {"display": "1 неделя", "code": "1W"},
    {"display": "1 месяц", "code": "1M"},
    {"display": "3 месяца", "code": "3M"},
    {"display": "6 месяцев", "code": "6M"},
    {"display": "12 месяцев", "code": "12M"}
]


class UserState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_timeframe = State()


@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        await message.reply("У вас нет доступа к этому боту")
        return
    chat_id = message.chat.id
    if chat_id not in users:
        users[chat_id] = {"currency": None, "timeframe": None}
        save_users_to_file()
        await message.answer(messages["START_MESSAGE"])
        await state.clear()
        await state.set_state(UserState.waiting_for_currency)
    else:
        await show_user_settings(message)


@dp.message(UserState.waiting_for_currency)
async def set_currency(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    users[chat_id]["currency"] = message.text.upper()
    save_users_to_file()

    if users[chat_id]["timeframe"] is not None:
        connection = users[chat_id]["connection"]
        await connection.end_connection()

        new_connection = TradingViewConnection(
            message.text.upper(),
            users[chat_id]["timeframe"]["code"])
        users[chat_id]["connection"] = new_connection
        asyncio.create_task(send_updates(new_connection, chat_id))

        await show_user_settings(message)
        return

    await message.answer(
        messages["SELECT_TIMEFRAME"],
        reply_markup=get_timeframe_keyboard(),
    )
    await state.clear()
    await state.set_state(UserState.waiting_for_timeframe)


@dp.message(UserState.waiting_for_timeframe)
async def set_timeframe(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    chosen_timeframe = next((tf for tf in timeframes
                             if tf["display"] == message.text), None)

    if chosen_timeframe:
        users[chat_id]["timeframe"] = chosen_timeframe
        save_users_to_file()

        connection = users[chat_id].get("connection")
        if connection:
            await connection.end_connection()

        new_connection = TradingViewConnection(
            users[chat_id]["currency"],
            users[chat_id]["timeframe"]["code"])
        asyncio.create_task(send_updates(new_connection, chat_id))
        users[chat_id]["connection"] = new_connection

        await message.answer(
            messages["SELECTED_TIMEFRAME"].format(message.text),
            reply_markup=ReplyKeyboardRemove(),
        )
        await show_user_settings(message)
        await state.clear()
    else:
        await message.answer(
            messages["TIMEFRAME_ERROR_1"],
            reply_markup=get_timeframe_keyboard(),
        )


async def show_user_settings(message: types.Message):
    chat_id = message.chat.id
    currency = users[chat_id]["currency"]
    timeframe = users[chat_id]["timeframe"]["display"]

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=messages["CHANGE_SYMBOL"],
                             callback_data="change_symbol")
    )
    builder.row(
        InlineKeyboardButton(text=messages["CHANGE_TIMEFRAME"],
                             callback_data="change_timeframe")
    )

    await message.answer(
        messages["SETTINGS"].format(currency, timeframe),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "change_symbol")
async def change_symbol(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(messages["CHANGE_SYMBOL_PR"])
    await state.clear()
    await state.set_state(UserState.waiting_for_currency)
    await callback.answer()


@dp.callback_query(F.data == "change_timeframe")
async def change_timeframe(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        messages["CHANGE_TIMEFRAME_PR"],
        reply_markup=get_timeframe_keyboard(),
    )
    await state.clear()
    await state.set_state(UserState.waiting_for_timeframe)
    await callback.answer()


def get_timeframe_keyboard():
    kb = []
    row = []
    for index, tf in enumerate(timeframes):
        button = KeyboardButton(text=tf["display"])
        row.append(button)
        if (index + 1) % 3 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                               one_time_keyboard=True)


@dp.message(Command("settings"))
async def settings_command(message: types.Message):
    if message.from_user.id not in OWNER_ID:
        await message.reply("У вас нет доступа к этому боту")
        return
    await show_user_settings(message)


async def main():
    load_users_from_file()
    load_messages_from_file()
    asyncio.create_task(create_server())
    for user in users:
        asyncio.create_task(send_updates(users[user]["connection"], user))
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
