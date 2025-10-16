import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
DB_PATH = "database/users.db"
SONG_PATH = "C:/Users/user/Desktop/melodybot/songs"
MAX_FILE_SIZE = 50 * 1024 * 1024
DAILY_LIMIT = 5

# logs qovluğunu yoxla, yoxdursa yarat
logs_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True)
LOG_FILE = os.path.join(logs_dir, "bot.log")

SEARCH_THRESHOLD = int(os.getenv("SEARCH_THRESHOLD", "50"))
