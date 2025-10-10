import os
from main import SONG_PATH

def test_song_files_exist():
    assert os.path.exists(os.path.join(SONG_PATH, "pop", "pop_song.mp3"))
    assert os.path.exists(os.path.join(SONG_PATH, "rock", "rock_song.mp3"))
    assert os.path.exists(os.path.join(SONG_PATH, "rap", "rap_song.mp3"))
    assert os.path.exists(os.path.join(SONG_PATH, "azeri", "azeri_song.mp3"))

def test_search_threshold():
    from main import song_list
    assert "pop_song" in song_list["pop"]  # Mahnı siyahıda olmalı