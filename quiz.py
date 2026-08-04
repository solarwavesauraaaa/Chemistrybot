# quiz.py
import sqlite3
from telegram import Bot
from database import register_poll
from config import DB_PATH, CHAT_ID

def get_all_questions():
    """Fetch all questions ordered by ID from DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, question, option_a, option_b, option_c, option_d, correct_option, explanation FROM questions ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        questions.append({
            "id": row[0],
            "question": row[1],
            "options": [row[2], row[3], row[4], row[5]],
            "correct_id": row[6],
            "explanation": row[7]
        })
    return questions

async def post_quiz_and_wait(bot: Bot, quiz: dict, current_no: int, total_count: int, chat_id: str = CHAT_ID, open_period: int = 25):
    """Posts numbered quiz, keeps it active for 25s, then closes it to reveal all votes"""
    try:
        # Title format: [NCERT Biology 2/22] Question?
        poll_title = f"[{current_no}/{total_count}] {quiz['question']}"
        if len(poll_title) > 300:  # Telegram poll question character limit handling
            poll_title = poll_title[:297] + "..."

        # Explanation check for Bulb Icon (Empty string par None hona zaroori hai)
        exp_text = quiz.get("explanation")
        if exp_text and isinstance(exp_text, str):
            exp_text = exp_text.strip()
            if len(exp_text) > 200:  # Telegram explanation limit (200 characters)
                exp_text = exp_text[:197] + "..."
        else:
            exp_text = None

        poll_message = await bot.send_poll(
            chat_id=chat_id,
            question=poll_title,
            options=quiz["options"],
            type="quiz",
            correct_option_id=quiz["correct_id"],
            explanation=exp_text if exp_text else None, # Bulb icon tabhi dikhega jab text ho
            is_anonymous=False, # Shows who voted for what
            open_period=open_period # Auto-closes poll after 25 seconds
        )
        
        # Register poll in DB to score correct votes
        register_poll(poll_message.poll.id, quiz["correct_id"])
        print(f"[QUIZ SENT] Question {current_no}/{total_count} posted successfully.")
        return poll_message
    except Exception as e:
        print(f"[ERROR SENDING QUIZ]: {e}")
        return None
