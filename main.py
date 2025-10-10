# main.py – MelodyBot-un giriş nöqtəsi (Aiogram 3.7+ uyğun)
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, LOG_FILE, SEARCH_THRESHOLD

# Logging konfiqurasiyası
if LOG_FILE:
    os.makedirs(os.path.dirname(LOG_FILE) or '.', exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        encoding="utf-8"
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
logger = logging.getLogger(__name__)

# Router və Bot obyekti
router = Router()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)

# /start əmri – Menyu ilə
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    logger.info(f"User {message.from_user.id} ({message.from_user.username}) started bot")
    
    # 2x2 keyboard – hər satır ayrıca siyahı
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Pop"), KeyboardButton(text="Rock")],
            [KeyboardButton(text="Rap"), KeyboardButton(text="Azəri")]
        ],
        resize_keyboard=True
    )
    
    await message.reply(
        f"Salam, <b>{message.from_user.first_name}</b>! 🎵 Mən <b>MelodyBot</b>-am. "
        "Janr seç və ya <i>/help</i> yaz:",
        reply_markup=keyboard
    )

# /help əmri
@router.message(Command("help"))
async def send_help(message: types.Message):
    logger.info(f"User {message.from_user.id} requested help")
    await message.reply(
        "🎶 <b>MelodyBot Köməyi</b>:\n"
        "<b>/start</b> - Janr menyusunu aç\n"
        "<b>Janr seç</b>: Pop, Rock, Rap, Azəri\n"
        f"<b>Axtarış</b>: Mahnı adı yaz (oxşarlıq həddi: {SEARCH_THRESHOLD}%)\n"
        "Gələcəkdə: Playlist yarat və paylaş!"
    )

# Əsas funksiya
async def main():
    logger.info("Bot işə düşür...")
    print("Bot işə düşür...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot dayandırıldı")
