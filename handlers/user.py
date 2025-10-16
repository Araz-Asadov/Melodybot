# handlers/user.py  — Aiogram 3.x üçün düzəldilmiş
import os
import json
import random
import logging
import sqlite3
from datetime import datetime

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SONG_PATH, DB_PATH

logger = logging.getLogger(__name__)
user_router = Router(name="user_router")

# Button mətni → fayl/genre map (diakritika problemi həll olundu)
TEXT_TO_GENRE = {
    "Azəri": "azeri",
    "Pop": "pop",
    "Rock": "rock",
    "Rap": "rap",
}

def _load_genre_json(genre: str) -> list:
    """Verilən genre üçün songs JSON-u yüklə."""
    json_file = os.path.join(SONG_PATH, f"song_{genre}.json")
    if not os.path.exists(json_file):
        return []
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_all_songs() -> list:
    songs = []
    for g in ("azeri", "pop", "rock", "rap"):
        songs.extend(_load_genre_json(g))
    return songs

def _pick_and_send_song_obj(song: dict) -> tuple[str, InlineKeyboardMarkup] | None:
    """Caption və inline keyboard hazırla."""
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sevimlilərə Əlavə Et", callback_data=f"add_fav_{song['id']}")]
        ]
    )
    caption = f"🎵 **{song['name']}** - {song['artist']} ({song['genre'].capitalize()})"
    return caption, markup

@user_router.message(F.text.in_(list(TEXT_TO_GENRE.keys()) + ["Təsadüfi Mahnı"]))
async def send_song(message: types.Message):
    try:
        btn_text = message.text
        if btn_text == "Təsadüfi Mahnı":
            songs = _load_all_songs()
        else:
            genre = TEXT_TO_GENRE[btn_text]  # "Azəri" → "azeri"
            songs = _load_genre_json(genre)

        if not songs:
            await message.reply("Mahnı tapılmadı – adminə de!")
            return

        song = random.choice(songs)
        file_path = os.path.join(SONG_PATH, song["path"])

        if not os.path.exists(file_path):
            await message.reply("Fayl tapılmadı – adminə müraciət edin.")
            logger.warning(f"Missing file for song_id={song.get('id')} path={file_path}")
            return

        caption, markup = _pick_and_send_song_obj(song)
        with open(file_path, "rb") as audio:
            await message.reply_audio(
                audio=audio,
                caption=caption,
                reply_markup=markup,
                title=song.get("name"),
                performer=song.get("artist"),
            )
        logger.info(f"Song {song['id']} sent to user {message.from_user.id}")

        # Stats-a dinləmə qeydi (opsional: play zamanı da yazmaq istəsən, saxla)
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO stats (user_id, song_id, timestamp) VALUES (?, ?, ?)",
                (message.from_user.id, song["id"], datetime.now()),
            )
            conn.commit()
            conn.close()
        except Exception as db_e:
            logger.error(f"Stats insert error: {db_e}")

    except Exception as e:
        logger.exception("send_song error")
        await message.reply("Səhv baş verdi – yenidən cəhd edin.")

# --- Sevimlilərə əlavə etmə callback-i ---
@user_router.callback_query(F.data.startswith("add_fav_"))
async def add_to_favorites(callback: types.CallbackQuery):
    try:
        song_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # UNIQUE(user_id, song_id) indexin varsa INSERT OR IGNORE problemsizdir
        c.execute(
            "INSERT OR IGNORE INTO playlist (user_id, song_id, added_at) VALUES (?, ?, ?)",
            (user_id, song_id, datetime.now()),
        )

        # Dinləmə stats (sevimliyə əlavə zamanı da qeyd etmək istəyirsənsə)
        c.execute(
            "INSERT INTO stats (user_id, song_id, timestamp) VALUES (?, ?, ?)",
            (user_id, song_id, datetime.now()),
        )

        conn.commit()
        conn.close()

        await callback.answer("✅ Sevimlilərə əlavə olundu!")
        logger.info(f"user={user_id} added song={song_id} to favorites")

    except Exception as e:
        logger.exception("add_to_favorites error")
        await callback.answer("Səhv baş verdi – yenidən cəhd edin.")

# --- /playlist və /favorites (alias) ---
@user_router.message(F.text.regexp(r"^/(playlist|favorites)$"))
async def show_playlist(message: types.Message):
    user_id = message.from_user.id
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT song_id, added_at FROM playlist WHERE user_id = ? ORDER BY added_at DESC LIMIT 50",
            (user_id,),
        )
        rows = c.fetchall()
        conn.close()

        if not rows:
            await message.reply("Sevimlilər siyahınız boşdur – əvvəlcə bir mahnı əlavə edin.")
            return

        # JSON-lardan title/artist tap
        songs = {s["id"]: s for s in _load_all_songs()}
        lines = ["📋 **Sizin Sevimlilər Siyahısı** (Ən yeni əvvəl):", ""]
        i = 1
        for song_id, added_at in rows:
            s = songs.get(song_id)
            if s:
                lines.append(f"{i}. **{s['name']}** - {s['artist']} ({s['genre']})")
                lines.append(f"   Tarix: {added_at}")
                lines.append("")
                i += 1

        text = "\n".join(lines)
        # Telegram 4096 limitinə yaxınlaşarsa, bir az kəs
        if len(text) > 3800:
            text = text[:3800] + "\n...\n(uzundur, qisaldıldı)"
        await message.reply(text)
        logger.info(f"Playlist shown to user {user_id} ({len(rows)} items)")

    except Exception as e:
        logger.exception("show_playlist error")
        await message.reply("Siyahını göstərməkdə səhv baş verdi.")

# --- /top10 ---
@user_router.message(F.text == "/top10")
async def show_top10(message: types.Message):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Son 30 gün
        c.execute(
            """
            SELECT song_id, COUNT(*) as cnt
            FROM stats
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY song_id
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
        rows = c.fetchall()
        conn.close()

        if not rows:
            await message.reply("Hələ statistika yoxdur – əvvəlcə bir neçə mahnı dinləyin.")
            return

        songs = {s["id"]: s for s in _load_all_songs()}
        lines = ["🏆 **Top 10 Populyar Mahnı** (Son 30 gün):", ""]
        rank = 1
        for song_id, cnt in rows:
            s = songs.get(song_id)
            if s:
                lines.append(f"{rank}. {s['name']} — {s['artist']}  •  {cnt} dinləmə")
                rank += 1

        await message.reply("\n".join(lines))
        logger.info(f"Top10 shown to user {message.from_user.id}")

    except Exception as e:
        logger.exception("show_top10 error")
        await message.reply("Top siyahısını göstərməkdə səhv baş verdi.")
