import os
import aiohttp
import asyncio
from config import SONG_PATH

# 1️⃣ Mahnı yollarını yoxlayır
print("=== Fayl mövcudluğu testi ===")
for genre in ["pop", "rock", "rap", "azeri"]:
    file_path = os.path.join(SONG_PATH, genre, f"{genre}_song.mp3")
    print(f"{genre.capitalize()}: {file_path} mövcuddur?:", os.path.exists(file_path))
    
    # Faylı açmaq testi
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                f.read(10)  # faylı bir az oxu
            print(f"{genre.capitalize()} faylı uğurla açıldı")
        except Exception as e:
            print(f"{genre.capitalize()} faylı açıla bilmədi:", e)
    else:
        print(f"{genre.capitalize()} faylı tapılmadı!")

# 2️⃣ Telegram API test
async def test_telegram():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegram.org") as resp:
                print("=== Telegram API Testi ===")
                print("Telegram API status:", resp.status)
    except Exception as e:
        print("Telegram API testində problem:", e)

asyncio.run(test_telegram())
