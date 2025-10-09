# -*- coding: utf-8 -*-
from config import BOT_TOKEN, ADMIN_ID, SONG_PATH, SEARCH_THRESHOLD
import os

print("Config test:")
print(f"BOT_TOKEN (ilk 6 simvol): {BOT_TOKEN[:6]}")
print(f"Admin ID: {ADMIN_ID}")
print(f"Song path: {SONG_PATH}")
print(f"Search threshold: {SEARCH_THRESHOLD}")
print(f"Path mövcuddurmu? {os.path.exists(SONG_PATH)}")
