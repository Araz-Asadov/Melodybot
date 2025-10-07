import aiogram
import sqlite3
from fuzzywuzzy import fuzz
from rapidfuzz.distance import Levenshtein

print("Bütün kitabxanalar quraşdırılıb və işləyir!")
print(f"Aiogram versiyası: {aiogram.__version__}")
