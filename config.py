import os

# Telegram API Configuration (Environment Variables se read karega)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "-1003939180704")

# Database Backup Channel ID (Optional)
BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID", "")

# Interval between quizzes (30 seconds)
INTERVAL_SECONDS = 30

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "biology_quiz.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Ensure required directories exist
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
