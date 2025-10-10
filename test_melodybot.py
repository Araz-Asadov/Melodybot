# test_melodybot.py
import os
import asyncio
import aiohttp
from config import SONG_PATH

# 1️⃣ Fayl yolları
paths = {
    "Pop": os.path.join(SONG_PATH, "pop", "pop_song.mp3"),
    "Rock": os.path.join(SONG_PATH, "rock", "rock_song.mp3"),
    "Rap": os.path.join(SONG_PATH, "rap", "rap_song.mp3"),
    "Azəri": os.path.join(SONG_PATH, "azeri", "azeri_song.mp3")
}

print("=== Fayl Yollarını Yoxlama ===")
for genre, path in paths.items():
    print(f"{genre}: {path}")
    print(f"{genre} mövcuddur?:", os.path.exists(path))
print("\n")

# 2️⃣ Faylları açma testi
print("=== Faylları Açma Testi ===")
for genre, path in paths.items():
    try:
        with open(path, "rb") as f:
            f.read(10)  # sadəcə ilk 10 baytı oxuyuruq
        print(f"{genre} faylı uğurla açıldı")
    except Exception as e:
        print(f"{genre} faylı açıla bilmir:", e)
print("\n")

# 3️⃣ Telegram serverinə qoşulma testi
async def test_telegram():
    print("=== Telegram API Testi ===")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegram.org") as resp:
                print("Telegram API status:", resp.status)
    except Exception as e:
        print("Telegram API-ə qoşula bilmədi:", e)

asyncio.run(test_telegram())
