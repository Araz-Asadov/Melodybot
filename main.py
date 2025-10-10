# main.py – MelodyBot (Aiogram 3.7+)
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, LOG_FILE, SEARCH_THRESHOLD, SONG_PATH

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

# /start əmri – 2x2 keyboard
@router.message(Command("start"))
async def send_welcome(message: types.Message):
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
    logger.info(f"İstifadəçi {message.from_user.id} ({message.from_user.username}) /start yazdı")

# /help əmri
@router.message(Command("help"))
async def send_help(message: types.Message):
    await message.reply(
        f"🎶 <b>MelodyBot Köməyi</b>:\n"
        "<b>/start</b> - Janr menyusunu aç\n"
        "<b>Janr seç</b>: Pop, Rock, Rap, Azəri\n"
        f"<b>Axtarış</b>: Mahnı adı yaz (oxşarlıq həddi: {SEARCH_THRESHOLD}%)\n"
        "Gələcəkdə: Playlist yarat və paylaş!"
    )
    logger.info(f"İstifadəçi {message.from_user.id} /help yazdı")

# Mahnı göndərmə funksiyası
async def send_song(message: types.Message, genre: str, filename: str, caption: str = None):
    file_path = os.path.join(SONG_PATH, genre, filename)
    if os.path.exists(file_path):
        audio = FSInputFile(file_path)
        await message.reply_audio(audio=audio, caption=caption)
        logger.info(f"{genre.capitalize()} mahnısı göndərildi: {file_path}")
    else:
        await message.reply(f"❌ Kədər, {genre.capitalize()} mahnısı tapılmadı! Adminə xəbər ver.")
        logger.error(f"{genre.capitalize()} mahnısı tapılmadı: {file_path}")

# Janr handler-ləri
@router.message(lambda m: m.text == "Pop")
async def handle_pop(message: types.Message):
    await send_song(message, "pop", "pop_song.mp3")

@router.message(lambda m: m.text == "Rock")
async def handle_rock(message: types.Message):
    await send_song(message, "rock", "rock_song.mp3")

@router.message(lambda m: m.text == "Rap")
async def handle_rap(message: types.Message):
    await send_song(message, "rap", "rap_song.mp3")

@router.message(lambda m: m.text == "Azəri")
async def handle_azeri(message: types.Message):
    await send_song(
        message,
        "azeri",
        "azeri_song.mp3",
        caption="🎵 Azərbaycan mahnısını xoşbəxt dinlə! 🇦🇿"
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