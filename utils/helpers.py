# utils/helpers.py – Köməkçi funksiyalar (MelodyBot Stable)
import sqlite3
import os
import json
from config import DB_PATH, SONG_PATH

def load_all_songs():
    """Bütün janrlardakı mahnıları JSON fayllardan yükləyir."""
    songs = []
    for genre in ["azeri", "pop", "rock", "rap"]:
        json_file = os.path.join(SONG_PATH, f"song_{genre}.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for s in data:
                        s["genre"] = genre  # Təhlükəsiz olsun deyə janrı əlavə et
                    songs.extend(data)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON səhvi: {genre} – {e}")
    return songs

def get_top_songs(limit=10, days=30):
    """Son X günün ən çox dinlənilən mahnılarını qaytarır."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = f"""
        SELECT song_id, COUNT(*) as cnt
        FROM stats
        WHERE timestamp > datetime('now', '-{days} days')
        GROUP BY song_id
        ORDER BY cnt DESC
        LIMIT ?
    """
    c.execute(query, (limit,))
    top = c.fetchall()
    conn.close()

    all_songs = load_all_songs()
    result = []
    for song_id, count in top:
        song = next((s for s in all_songs if s["id"] == song_id), None)
        if song:
            result.append(f"{song['name']} - {song['artist']} ({count} dinləmə)")

    return result

from datetime import date
import sqlite3
from config import DB_PATH, DAILY_LIMIT

def check_limit(user_id: int) -> bool:
    """İstifadəçinin gündəlik limitini yoxla"""
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count, is_premium FROM daily_limit WHERE user_id = ? AND date = ?", (user_id, today))
    result = c.fetchone()

    # Premium istifadəçi – limitsiz
    if result and result[1] == 1:
        conn.close()
        return True

    # Yeni gün – yeni qeyd
    if not result:
        c.execute("INSERT INTO daily_limit (user_id, date, count, is_premium) VALUES (?, ?, 0, 0)", (user_id, today))
        conn.commit()
        result = (0, 0)

    if result[0] >= DAILY_LIMIT:
        conn.close()
        return False  # limit dolub

    # Count artır
    c.execute("UPDATE daily_limit SET count = count + 1 WHERE user_id = ? AND date = ?", (user_id, today))
    conn.commit()
    conn.close()
    return True
