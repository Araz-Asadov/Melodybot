# config.py
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8225756508:AAGJdEemrCfPiEmIRGBYgMNwTvsa7NapYks")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
DB_PATH = "database/users.db"
SONG_PATH = "C:/Users/user/Desktop/melodybot/songs"
MAX_FILE_SIZE = 50 * 1024 * 1024
DAILY_LIMIT = 5
LOG_FILE = os.path.join(os.getcwd(), "logs", "bot.log")
SEARCH_THRESHOLD = int(os.getenv("SEARCH_THRESHOLD", "80"))