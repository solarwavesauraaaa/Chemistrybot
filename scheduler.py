# scheduler.py
import asyncio
import sqlite3
from telegram import Bot
from config import CHAT_ID, INTERVAL_SECONDS, DB_PATH
from quiz import post_quiz_and_wait
from leaderboard import build_leaderboard_text
from database import reset_session_scores, get_next_chapter_index, update_chapter_index

is_quiz_running = False

def get_questions_for_today():
    """Database se agle chapter ke questions aur uska naam nikalta hai"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Saare available unique chapters ki list
    cursor.execute('SELECT DISTINCT chapter_name FROM questions ORDER BY id ASC')
    chapters = [row[0] for row in cursor.fetchall()]

    if not chapters:
        conn.close()
        return None, []

    current_idx = get_next_chapter_index()
    
    # Agar saare chapters khatam ho jayein toh dobara 1st chapter se repeat hoga
    if current_idx >= len(chapters):
        current_idx = 0

    selected_chapter = chapters[current_idx]

    cursor.execute(
        'SELECT id, question, option_a, option_b, option_c, option_d, correct_option, explanation FROM questions WHERE chapter_name = ? ORDER BY id ASC',
        (selected_chapter,)
    )
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

    return selected_chapter, questions, current_idx

async def run_quiz_session(bot: Bot):
    global is_quiz_running
    
    if is_quiz_running:
        return

    is_quiz_running = True
    chapter_name, questions, current_idx = get_questions_for_today()

    if not questions:
        await bot.send_message(chat_id=CHAT_ID, text="❌ Database me koi questions nahi mile.")
        is_quiz_running = False
        return

    reset_session_scores()
    total_questions = len(questions)

    await bot.send_message(
        chat_id=CHAT_ID, 
        text=f"🚀 *DAILY NCERT PYQ TEST STARTED!*\n\n📖 *Chapter:* `{chapter_name.upper()}`\n📚 *Questions:* `{total_questions}`\n⏱ *Interval:* `{INTERVAL_SECONDS} seconds`", 
        parse_mode="Markdown"
    )
    await asyncio.sleep(2)

    try:
        for index, quiz in enumerate(questions, start=1):
            if not is_quiz_running:
                break

            await post_quiz_and_wait(
                bot=bot,
                chat_id=CHAT_ID,
                quiz=quiz,
                current_no=index,
                total_count=total_questions,
                open_period=INTERVAL_SECONDS
            )
            await asyncio.sleep(INTERVAL_SECONDS + 1)

    except Exception as e:
        print(f"[SCHEDULER ERROR]: {e}")
    finally:
        if is_quiz_running:
            session_result = f"🎉 *{chapter_name.upper()} TEST COMPLETED!* 🎉\n\n" + build_leaderboard_text(is_session_only=True)
            await bot.send_message(chat_id=CHAT_ID, text=session_result, parse_mode="Markdown")
            
            # Agle din ke liye next chapter set kar dein
            update_chapter_index(current_idx + 1)

        is_quiz_running = False
