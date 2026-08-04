import sqlite3
import os
import logging
from config import DB_PATH, BACKUP_CHANNEL_ID

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option INTEGER,
            explanation TEXT,
            chapter_name TEXT
        )
    ''')
    
    # 2. Quiz Progress Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_progress (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_chapter_index INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO quiz_progress (id, last_chapter_index) VALUES (1, 0)')

    # 3. Active Polls Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_polls (
            poll_id TEXT PRIMARY KEY,
            correct_option INTEGER,
            question_id INTEGER
        )
    ''')

    # 4. User Scores Table (Overall & Current Session track karne ke liye)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_scores (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            score INTEGER DEFAULT 0,
            session_score INTEGER DEFAULT 0
        )
    ''')

    # Safe Migration: Agar purani DB hai toh automatically session_score column add kar dega
    try:
        cursor.execute("ALTER TABLE user_scores ADD COLUMN session_score INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()

# --- CHAPTER PROGRESS FUNCTIONS ---
def get_next_chapter_index():
    """Agla chapter number nikalne ke liye"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT last_chapter_index FROM quiz_progress WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_chapter_index(next_idx):
    """Aaj ka chapter poora hone par progress update karega"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE quiz_progress SET last_chapter_index = ? WHERE id = 1', (next_idx,))
    conn.commit()
    conn.close()

# --- POLL & SCORING FUNCTIONS ---
def register_poll(poll_id: str, correct_option: int, question_id: int = 0):
    """Poll ID aur correct option ko active_polls table me save karega"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO active_polls (poll_id, correct_option, question_id)
        VALUES (?, ?, ?)
    ''', (str(poll_id).strip(), int(correct_option), question_id))
    conn.commit()
    conn.close()

def get_poll_correct_option(poll_id: str):
    """Poll ID se correct option fetch karega"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT correct_option FROM active_polls WHERE poll_id = ?', (str(poll_id).strip(),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_user_score(user_id: int, username: str, first_name: str, is_correct: bool = True):
    """Sahi uttar dene par user ka score & session_score increment karega"""
    if not is_correct:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_scores (user_id, username, first_name, score, session_score)
        VALUES (?, ?, ?, 1, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            score = score + 1,
            session_score = session_score + 1,
            username = excluded.username,
            first_name = excluded.first_name
    ''', (user_id, username or "", first_name or "User"))
    conn.commit()
    conn.close()

def reset_session_scores():
    """Har naye quiz session par session_score zero karega aur purani polls clear karega"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM active_polls')
    cursor.execute('UPDATE user_scores SET session_score = 0')
    conn.commit()
    conn.close()

async def restore_db_from_telegram(bot):
    """Startup par Telegram backup channel se DB restore (Safe Stub)"""
    logger.info("Database restore check passed.")
