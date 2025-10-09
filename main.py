# main.py
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from config import API_TOKEN
import asyncio

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(f"Salam, {message.from_user.first_name}! Mən Melodybotam. /help üçün kömək al.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())