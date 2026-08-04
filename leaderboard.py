import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

def build_leaderboard_text(is_session_only=False):
    """
    Leaderboard text generate karega.
    user_scores table se scores fetch karta hai.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check table structure dynamically for fallback
        cursor.execute("PRAGMA table_info(user_scores)")
        columns = [column[1] for column in cursor.fetchall()]

        # Determine score column (score or session_score)
        score_column = "session_score" if "session_score" in columns and is_session_only else "score"

        cursor.execute(f'''
            SELECT first_name, {score_column} 
            FROM user_scores 
            WHERE {score_column} > 0 
            ORDER BY {score_column} DESC 
            LIMIT 10
        ''')
        rows = cursor.fetchall()

        if not rows:
            return "📊 *QUIZ LEADERBOARD*\n\nAbhi tak kisi user ke scores record nahi hue hain."

        medals = ["🥇", "🥈", "🥉"]
        title = "🎉 *TEST LEADERBOARD* 🎉" if is_session_only else "🏆 *OVERALL LEADERBOARD* 🏆"
        text = f"{title}\n\n"

        for rank, (name, score) in enumerate(rows, 1):
            medal = medals[rank - 1] if rank <= 3 else "👤"
            text += f"{medal} *{name}* — `{score}` pts\n"

        conn.close()
        return text

    except Exception as e:
        logger.error(f"Error building leaderboard: {e}")
        conn.close()
        return "❌ Leaderboard generate karne me error aaya."
