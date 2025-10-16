# main.py – MelodyBot (Stable FSM + Admin + YouTube MP3 Converter)
import asyncio
import logging
import os
import shutil
import json
import random
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DB_PATH, SONG_PATH
from database.init_db import init_database
from utils.helpers import get_top_songs
import yt_dlp  # 🔹 YouTube MP3 çevirmək üçün əlavə olundu

# --- Xəbərdarlıqları söndür ---
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- Logging konfiqurasiyası ---
if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    encoding="utf-8",
    force=True
)
logger = logging.getLogger(__name__)

# --- Bot və Dispatcher ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# --- Admin router-i əlavə et ---
from handlers import admin
dp.include_router(admin.router)

# --- Verilənlər bazası və backup ---
init_database()
def backup_database():
    os.makedirs("backup", exist_ok=True)
    backup_path = f"backup/users_{datetime.now().strftime('%Y%m%d')}.db"
    shutil.copy(DB_PATH, backup_path)
    logger.info(f"DB backup yaradıldı: {backup_path}")
backup_database()

# --- JSON mahnıları yüklə ---
song_data = {}
for genre in ["pop", "rock", "rap", "azeri"]:
    json_file = os.path.join(SONG_PATH, f"song_{genre}.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                song_data[genre] = json.load(f)
            logger.info(f"{genre.capitalize()} janrından {len(song_data[genre])} mahnı yükləndi")
        except json.JSONDecodeError as e:
            logger.error(f"{genre} JSON səhvi: {e}")
    else:
        song_data[genre] = []
        logger.warning(f"{genre} JSON tapılmadı: {json_file}")

# --- /start əmri ---
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Pop"), KeyboardButton(text="Rock")],
            [KeyboardButton(text="Rap"), KeyboardButton(text="Azəri")],
            [KeyboardButton(text="Təsadüfi Mahnı")]
        ],
        resize_keyboard=True
    )
    await message.reply(
        f"Salam, <b>{message.from_user.first_name}</b>! 🎵 Mən <b>MelodyBot</b>-am.\n"
        f"Janr seç və ya /help yaz:",
        reply_markup=keyboard
    )
    logger.info(f"User {message.from_user.id} started the bot")

# --- /help əmri ---
@router.message(Command("help"))
async def send_help(message: types.Message):
    await message.reply(
        "🎶 <b>MelodyBot Köməyi</b>\n\n"
        "<b>/start</b> – Menyu aç\n"
        "<b>/favorites</b> – Sevimli mahnıları gör\n"
        "<b>/playlist</b> – Playlist siyahısı\n"
        "<b>/top10</b> – Ən populyar mahnılar\n"
        "<b>/delete_data</b> – Bütün məlumatları sil\n"
        "<b>Janr seç:</b> Pop, Rock, Rap, Azəri, Təsadüfi Mahnı\n"
        "<b>💡 YouTube Link göndər:</b> videonun MP3 versiyası gələcək 🎧",
        parse_mode="HTML"
    )

# --- Mahnı göndərmə funksiyası ---
async def send_song(message: types.Message, genre: str = None):
    user_id = message.from_user.id

    if genre:
        if genre not in song_data or not song_data[genre]:
            await message.reply(f"❌ {genre.capitalize()} janrında mahnı yoxdur.")
            return
        songs = song_data[genre]
    else:
        songs = [song for genre_list in song_data.values() for song in genre_list]

    if not songs:
        await message.reply("❌ Heç bir mahnı tapılmadı.")
        return

    song = random.choice(songs)
    file_path = os.path.join(SONG_PATH, song["path"])
    if os.path.exists(file_path):
        audio = FSInputFile(file_path)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Sevimlilərə əlavə et", callback_data=f"add_fav_{song['id']}")]
            ]
        )
        await message.reply_audio(
            audio=audio,
            caption=f"🎵 <b>{song['name']}</b> – {song['artist']} ({song['genre'].capitalize()})",
            reply_markup=markup
        )
        logger.info(f"Song sent: {song['name']} ({song['genre']}) to user {user_id}")
    else:
        await message.reply("❌ Fayl tapılmadı!")

# --- Janr handler-ləri ---
@router.message(F.text == "Pop")
async def handle_pop(message: types.Message):
    await send_song(message, "pop")

@router.message(F.text == "Rock")
async def handle_rock(message: types.Message):
    await send_song(message, "rock")

@router.message(F.text == "Rap")
async def handle_rap(message: types.Message):
    await send_song(message, "rap")

@router.message(F.text == "Azəri")
async def handle_azeri(message: types.Message):
    await send_song(message, "azeri")

@router.message(F.text == "Təsadüfi Mahnı")
async def handle_random(message: types.Message):
    await send_song(message)

# --- YouTube linklər üçün Converter ---
@router.message(F.text.regexp(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"))
async def youtube_to_mp3(message: types.Message):
    url = message.text.strip()
    status = await message.reply("🎧 YouTube link tapıldı, mahnı hazırlanır...")

    output_dir = os.path.join(SONG_PATH, "downloads")
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown")
            filename = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(filename)[0] + ".mp3"

        if os.path.exists(mp3_path):
            await message.reply_audio(
                FSInputFile(mp3_path),
                caption=f"🎵 <b>{title}</b>\nYouTube-dan MP3 formatında yükləndi.",
                parse_mode=ParseMode.HTML
            )
            await status.delete()
        else:
            await status.edit_text("❌ Fayl tapılmadı – çevirmə uğursuz oldu.")

    except Exception as e:
        await status.edit_text("⚠️ Səhv baş verdi, linki yenidən yoxlayın.")
        logger.error(f"YouTube Converter error: {e}")

# --- Callback: Sevimlilərə əlavə et ---
@router.callback_query(F.data.startswith("add_fav_"))
async def add_to_favorites(callback: types.CallbackQuery):
    import sqlite3
    try:
        song_id = int(callback.data.replace("add_fav_", ""))
        user_id = callback.from_user.id
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("BEGIN")
        c.execute("INSERT OR IGNORE INTO playlist (user_id, song_id, added_at) VALUES (?, ?, ?)",
                  (user_id, song_id, datetime.now().isoformat()))
        c.execute("INSERT INTO stats (user_id, song_id, timestamp) VALUES (?, ?, ?)",
                  (user_id, song_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        await callback.answer("✅ Sevimlilərə əlavə olundu!")
    except Exception as e:
        logger.error(f"Fav error: {e}")
        await callback.answer("❌ Səhv baş verdi.")

# --- /favorites əmri ---
@router.message(Command("favorites"))
async def show_favorites(message: types.Message):
    import sqlite3
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT song_id FROM playlist WHERE user_id = ? ORDER BY added_at DESC LIMIT 50", (user_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        await message.reply("⭐ Sevimli mahnılarınız yoxdur.")
        return

    all_songs = [s for g in song_data.values() for s in g]
    text = "⭐ <b>Sevimli Mahnılar:</b>\n\n"
    for sid, in rows:
        song = next((s for s in all_songs if s["id"] == sid), None)
        if song:
            text += f"🎵 {song['name']} – {song['artist']} ({song['genre'].capitalize()})\n"
    await message.reply(text, parse_mode="HTML")

# --- /top10 əmri ---
@router.message(Command("top10"))
async def show_top10(message: types.Message):
    top = get_top_songs(10)
    if not top:
        await message.reply("📉 Hələ statistika yoxdur.")
        return
    text = "🏆 <b>Top 10 Populyar Mahnı:</b>\n\n" + "\n".join(top)
    await message.reply(text, parse_mode="HTML")

# --- /delete_data əmri ---
@router.message(Command("delete_data"))
async def delete_data(message: types.Message):
    import sqlite3
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM playlist WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM stats WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    await message.reply("✅ Bütün məlumatlar silindi.")
    logger.info(f"User {user_id} data deleted.")

# --- Bot işə düşür ---
async def main():
    logger.info("🎵 MelodyBot is running...")
    print("🎵 MelodyBot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot dayandırıldı.")
