# bot.py
import os
import asyncio
import datetime
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, PollAnswerHandler, filters, ContextTypes
from config import BOT_TOKEN, CHAT_ID, BACKUP_CHANNEL_ID
from database import init_db, get_poll_correct_option, update_user_score, restore_db_from_telegram
from leaderboard import build_leaderboard_text
from admin import handle_document
from scheduler import run_quiz_session
from questions import load_all_github_questions  # <--- GitHub questions loader imported

# --- DUMMY HTTP SERVER FOR RENDER PORT BINDING ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        return  # Keep console logs clean

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()
# --------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 NCERT Chemistry Bot Ready!\n\nCommands:\n/start_quiz - Start MCQ Test\n/leaderboard - Check Ranks")

async def trigger_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers quiz manually when /start_quiz command is used"""
    asyncio.create_task(run_quiz_session(context.bot))

async def text_trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers quiz only when exact text 'start quiz' is sent"""
    if update.message and update.message.text:
        text = update.message.text.strip().lower()
        if text in ["start quiz", "start_quiz", "quiz start"]:
            asyncio.create_task(run_quiz_session(context.bot))

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    board_text = build_leaderboard_text()
    await update.message.reply_text(board_text, parse_mode="Markdown")

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user = answer.user
    selected_options = answer.option_ids

    if not selected_options:
        return

    correct_option = get_poll_correct_option(poll_id)
    if correct_option is not None and selected_options[0] == correct_option:
        update_user_score(
            user_id=user.id,
            first_name=user.first_name,
            username=user.username
        )

# Job Function for Daily Quiz Trigger
async def scheduled_quiz_job(context: ContextTypes.DEFAULT_TYPE):
    await run_quiz_session(context.bot)

# Job Function to restore DB on bot startup
async def restore_db_job(context: ContextTypes.DEFAULT_TYPE):
    await restore_db_from_telegram(context.bot)

def main():
    # 1. Start Dummy Web Server in Background Thread (Fixes Render Port Scan)
    server_thread = Thread(target=run_health_check_server, daemon=True)
    server_thread.start()

    # 2. Init DB local structure & Load GitHub questions
    init_db()
    load_all_github_questions()  # <--- GitHub Folder (questions/*.txt) se questions auto load karega

    # 3. Build Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("start_quiz", trigger_quiz_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_trigger_handler))
    app.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), handle_document))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    # --- RESTORE DATABASE ON STARTUP ---
    if app.job_queue:
        app.job_queue.run_once(restore_db_job, 2)

    # --- DAILY 10:00 PM (22:00 IST) SCHEDULER (Native JobQueue) ---
    tz = pytz.timezone("Asia/Kolkata")
    target_time = datetime.time(hour=21, minute=0, second=0, tzinfo=tz)
    
    # Schedule daily quiz
    if app.job_queue:
        app.job_queue.run_daily(scheduled_quiz_job, time=target_time)
    # -------------------------------------------------------------

    print("=" * 50)
    print("NCERT Biology Bot Started Successfully!")
    print("Health check server active on port binding!")
    print("Auto-Restore & Daily Auto-Quiz (10:00 PM IST) Scheduled!")
    print("=" * 50)
    
    # drop_pending_updates=True se conflict errors aur bot duplicate instance crash fix honge
    app.run_polling(poll_interval=1.0, drop_pending_updates=True)

if __name__ == "__main__":
    main()
