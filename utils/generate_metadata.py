from mutagen.mp3 import MP3
import json
import os

# SONG_PATH = 'songs'  # Əgər config.py yoxdursa, bu yolu istifadə et
SONG_PATH = os.path.join(os.getcwd(), "songs")  # mövcud qovluq əsasında

# Janrları təyin et
genres = ["azeri", "pop", "rock", "rap"]

for genre in genres:
    songs = []  # Hər janr üçün ayrıca siyahı
    genre_path = os.path.join(SONG_PATH, genre)

    if not os.path.exists(genre_path):
        print(f"⚠️ {genre_path} qovluğu yoxdur, keçildi.")
        continue

    # MP3 fayllarını dolaş
    for i, filename in enumerate(os.listdir(genre_path), 1):
        if filename.endswith(".mp3"):
            file_path = os.path.join(genre_path, filename)
            audio = MP3(file_path)

            # Metadata çıxar, yoxdursa default dəyər istifadə et
            song_name = str(audio.get("TIT2", filename[:-4]))
            song_artist = str(audio.get("TPE1", "Unknown Artist"))

            song = {
                "id": i,
                "name": song_name,
                "artist": song_artist,
                "genre": genre,
                "path": os.path.join(genre, filename)
            }
            songs.append(song)

    # JSON faylı yaradılır
    os.makedirs(SONG_PATH, exist_ok=True)
    json_file = os.path.join(SONG_PATH, f"song_{genre}.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"✅ {genre} mahnıları JSON-a əlavə olundu ({len(songs)} mahnı).")
