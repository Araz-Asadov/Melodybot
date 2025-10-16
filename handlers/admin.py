# handlers/admin.py – Sadə Admin Panel (FSM + Limit)
import os
import json
import logging
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, SONG_PATH
from utils.helpers import load_all_songs

logger = logging.getLogger(__name__)
router = Router()

# --- Admin yoxlaması ---
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# --- FSM vəziyyətləri ---
class AddSong(StatesGroup):
    file = State()
    name = State()
    artist = State()
    genre = State()

# --- /stats əmri ---
@router.message(F.text == "/stats")
async def admin_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Bu əmr yalnız admin üçündür!")
        return
    from utils.helpers import get_top_songs
    top_songs = get_top_songs(10)
    text = "📊 <b>Admin Statistika</b>\n\n"
    text += "🏆 <b>Top 10 mahnı:</b>\n" + "\n".join(top_songs) if top_songs else "Hələ məlumat yoxdur."
    await message.reply(text, parse_mode="HTML")
    logger.info(f"Admin {message.from_user.id} statistika baxdı")

# --- /add əmri: FSM başlanğıcı ---
@router.message(F.text == "/add")
async def add_song_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Bu əmr yalnız admin üçündür!")
        return
    await state.set_state(AddSong.file)
    await message.reply("📤 MP3 faylını göndər:")

# --- 1. Fayl qəbul et ---
@router.message(F.content_type == "audio", AddSong.file)
async def process_file(message: types.Message, state: FSMContext):
    file_name = message.audio.file_name
    if not file_name.endswith(".mp3"):
        await message.reply("❌ Yalnız MP3 fayllar qəbul olunur.")
        return
    file = await message.bot.get_file(message.audio.file_id)
    dest = os.path.join(SONG_PATH, file_name)
    await message.bot.download_file(file.file_path, dest)
    await state.update_data(path=file_name)
    await state.set_state(AddSong.name)
    await message.reply("✅ Fayl qəbul olundu. İndi mahnının adını yaz:")

# --- 2. Ad al ---
@router.message(AddSong.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddSong.artist)
    await message.reply("🎤 İndi sənətçi adını yaz:")

# --- 3. Artist al ---
@router.message(AddSong.artist)
async def process_artist(message: types.Message, state: FSMContext):
    await state.update_data(artist=message.text.strip())
    await state.set_state(AddSong.genre)
    await message.reply("🎶 Janrı yaz (pop, rock, rap, azeri):")

# --- 4. Janr və tamamla ---
@router.message(AddSong.genre)
async def process_genre(message: types.Message, state: FSMContext):
    genre = message.text.lower().strip()
    if genre not in ["pop", "rock", "rap", "azeri"]:
        await message.reply("❌ Yanlış janr. pop / rock / rap / azeri yaz.")
        return

    data = await state.get_data()
    song_path = os.path.join(SONG_PATH, f"song_{genre}.json")
    songs = []
    if os.path.exists(song_path):
        with open(song_path, "r", encoding="utf-8") as f:
            songs = json.load(f)

    new_id = max([s["id"] for s in songs], default=0) + 1
    new_song = {
        "id": new_id,
        "name": data["name"],
        "artist": data["artist"],
        "genre": genre,
        "path": data["path"]
    }
    songs.append(new_song)

    with open(song_path, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    await message.reply(f"✅ Mahnı əlavə olundu:\n🎵 {data['name']} - {data['artist']} ({genre})")
    await state.clear()
    logger.info(f"Admin {message.from_user.id} mahnı əlavə etdi: {data['name']}")
