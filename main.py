# main.py – MelodyBot (Aiogram 3.7+)
import asyncio
import logging
import os
import json
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, LOG_FILE, SEARCH_THRESHOLD, SONG_PATH
from rapidfuzz import fuzz

# Mahnı və sevimli siyahısını saxlama (xatirə kimi sadə dictionary)
favorites = {}  # user_id -> list of song IDs

# Mahnı siyahısını JSON-dan yüklə və yoxla
song_data = {}
for genre in ["pop", "rock", "rap", "azeri"]:
    json_file = os.path.join(SONG_PATH, f"song_{genre}.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                song_data[genre] = json.load(f)
            logging.info(f"{genre.capitalize()} JSON-u yükləndi: {len(song_data[genre])} mahnı")
        except json.JSONDecodeError as e:
            logging.error(f"{genre} JSON səhvi: {e}")
    else:
        logging.warning(f"{genre} JSON faylı tapılmadı: {json_file}")

# Logging konfiqurasiyası
if LOG_FILE:
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        encoding="utf-8",
        force=True  # Köhnə handler-ləri silir və yenisini təmin edir
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
logger = logging.getLogger(__name__)

# Bot və Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Router
router = Router()
dp.include_router(router)

# /start əmri
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
        "<b>Janr seç</b>: Pop, Rock, Rap, Azəri, Təsadüfi Mahnı\n"
        f"<b>Axtarış</b>: Mahnı adı yaz (oxşarlıq həddi: {SEARCH_THRESHOLD}%)\n"
        "Gələcəkdə: Playlist yarat və paylaş!"
    )
    logger.info(f"İstifadəçi {message.from_user.id} /help yazdı")

# Mahnı göndərmə funksiyası
async def send_song(message: types.Message, genre: str = None):
    if genre:
        if genre not in song_data or not song_data[genre]:
            await message.reply(f"❌ {genre.capitalize()} mahnıları üçün məlumat yoxdur!")
            logger.error(f"{genre.capitalize()} mahnıları tapılmadı")
            return
        songs = song_data[genre]
    else:
        # Təsadüfi Mahnı üçün bütün janrlardan birləşdir
        songs = [song for genre_list in song_data.values() for song in genre_list]
        if not songs:
            await message.reply("❌ Heç bir mahnı tapılmadı!")
            logger.error("Heç bir mahnı yüklənmədi")
            return

    song = random.choice(songs)
    file_path = os.path.join(SONG_PATH, song["path"])
    if os.path.exists(file_path):
        audio = FSInputFile(file_path)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Sevimlilərə Əlavə Et", callback_data=f"add_fav_{song['id']}")]
        ])
        await message.reply_audio(
            audio=audio,
            caption=f"🎵 <b>{song['name']}</b> - {song['artist']} ({song['genre'].capitalize()})",
            reply_markup=markup,
            title=song['name'],
            performer=song['artist']
        )
        logger.info(f"{song['genre'].capitalize()} mahnısı göndərildi: {song['name']}")
    else:
        await message.reply(f"❌ {song['genre'].capitalize()} mahnısı faylı tapılmadı!")
        logger.error(f"Fayl tapılmadı: {file_path}")

# Janr handler-ləri
@router.message(lambda m: m.text == "Pop")
async def handle_pop(message: types.Message):
    await send_song(message, "pop")

@router.message(lambda m: m.text == "Rock")
async def handle_rock(message: types.Message):
    await send_song(message, "rock")

@router.message(lambda m: m.text == "Rap")
async def handle_rap(message: types.Message):
    await send_song(message, "rap")

@router.message(lambda m: m.text == "Azəri")
async def handle_azeri(message: types.Message):
    await send_song(message, "azeri")

# Təsadüfi Mahnı handler-ı
@router.message(lambda m: m.text == "Təsadüfi Mahnı")
async def handle_random(message: types.Message):
    await send_song(message)

# Axtarış handler-ı
@router.message()
async def search_song(message: types.Message):
    query = message.text.lower()
    best_match = None
    best_score = SEARCH_THRESHOLD
    best_genre = None

    for genre, songs in song_data.items():
        for song in songs:
            score = fuzz.ratio(query, song["name"].lower())
            if score >= best_score:
                best_score = score
                best_match = song
                best_genre = genre

    if best_match:
        await send_song(message, best_genre)
        logger.info(f"Axtarış: '{query}' -> {best_genre}/{best_match['name']} (Score: {best_score}%)")
    else:
        await message.reply(f"❌ '{query}' üçün uyğun mahnı tapılmadı!")
        logger.info(f"Axtarış uğursuz: '{query}'")

# Callback handler - Sevimlilərə əlavə et
@router.callback_query(lambda c: c.data.startswith("add_fav_"))
async def add_to_favorites(callback: types.CallbackQuery):
    song_id = int(callback.data.replace("add_fav_", ""))
    user_id = callback.from_user.id

    # İstifadəçinin sevimli siyahısını yoxla və ya yarad
    if user_id not in favorites:
        favorites[user_id] = []
    if song_id not in favorites[user_id]:
        # Mahnını tap
        song = next((s for g in song_data.values() for s in g if s["id"] == song_id), None)
        if song:
            favorites[user_id].append(song_id)
            await callback.answer(f"✅ '{song['name']}' sevimlilərə əlavə olundu!")
            logger.info(f"İstifadəçi {user_id} {song['name']} mahnısını sevimlilərə əlavə etdi")
        else:
            await callback.answer("❌ Mahnı tapılmadı!")
            logger.error(f"Sevimli əlavə edərkən səhv: Mahnı ID {song_id} tapılmadı")
    else:
        await callback.answer("⛔ Bu mahnı artıq sevimlilərdədir!")
        logger.info(f"İstifadəçi {user_id} təkrar əlavə etməyə çalışdı: {song_id}")

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