# admin.py
import os
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes
from parser import parse_txt_questions
from config import DB_PATH, UPLOADS_DIR

def clear_old_questions():
    """Nayi file aane par puraane questions clear karne ke liye"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions')
    conn.commit()
    conn.close()

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """File receive karke parse aur save karta hai"""
    try:
        file = await update.message.document.get_file()
        
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)
            
        file_path = os.path.join(UPLOADS_DIR, update.message.document.file_name)
        await file.download_to_drive(file_path)

        # 1. Text file se questions parse karein
        questions = parse_txt_questions(file_path)
        
        if questions:
            # 2. Clear old questions
            clear_old_questions()
            
            # 3. Insert new questions
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            for q in questions:
                cursor.execute('''
                    INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (q['question'], q['options'][0], q['options'][1], q['options'][2], q['options'][3], q['correct_id'], q['explanation']))
            conn.commit()
            conn.close()

            await update.message.reply_text(f"✅ Success! `{len(questions)}` new Chemsitry MCQs loaded. Purana database clear kar diya gaya hai.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ File format sahi nahi tha ya parser error. Questions parse nahi ho paaye.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error processing file: `{str(e)}`", parse_mode="Markdown")
