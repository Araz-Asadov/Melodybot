# config.py
from dotenv import load_dotenv
import os

load_dotenv()  # .env-dən yüklə
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_PATH = "database/users.db"
SONG_PATH = "songs/"
MAX_FILE_SIZE = 50 * 1024 * 1024
DAILY_LIMIT = 5
LOG_FILE = "bot.log"
SEARCH_THRESHOLD = int(os.getenv("SEARCH_THRESHOLD", 80))  # Varsayılan: 80