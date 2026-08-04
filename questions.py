# questions.py
import os
import glob
import re
import sqlite3
from config import DB_PATH

def parse_and_insert_txt_content(content: str, chapter_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    blocks = [b.strip() for b in re.split(r'\n\s*\n', content.strip()) if b.strip()]
    inserted_count = 0

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 5:
            continue

        q_lines, option_lines, ans_line = [], [], ""
        for line in lines:
            if re.match(r'^(Ans|Answer|Correct)\s*[:\-=]', line, re.IGNORECASE):
                ans_line = line
            elif re.match(r'^(A\)|A\.|B\)|B\.|C\)|C\.|D\)|D\.|1\)|1\.|2\)|2\.|3\)|3\.|4\)|4\.)\s*', line, re.IGNORECASE):
                option_lines.append(line)
            else:
                if not option_lines:
                    q_lines.append(line)

        q_text = "\n".join(q_lines)
        q_text = re.sub(r'^(Q:|\d+\.)\s*', '', q_text, flags=re.IGNORECASE).strip()

        if len(option_lines) < 4:
            continue

        op_a = re.sub(r'^(A\)|A\.|1\)|1\.)\s*', '', option_lines[0], flags=re.IGNORECASE).strip()
        op_b = re.sub(r'^(B\)|B\.|2\)|2\.)\s*', '', option_lines[1], flags=re.IGNORECASE).strip()
        op_c = re.sub(r'^(C\)|C\.|3\)|3\.)\s*', '', option_lines[2], flags=re.IGNORECASE).strip()
        op_d = re.sub(r'^(D\)|D\.|4\)|4\.)\s*', '', option_lines[3], flags=re.IGNORECASE).strip()

        correct_opt = 0
        exp_text = ""

        if ans_line:
            ans_match = re.search(r'^(?:Ans|Answer|Correct)\s*[:\-=]\s*([A-D1-4])', ans_line, re.IGNORECASE)
            if ans_match:
                ans_str = ans_match.group(1).upper()
                mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3, '1': 0, '2': 1, '3': 2, '4': 3}
                correct_opt = mapping.get(ans_str, 0)

            exp_match = re.search(r'\[(.*?)\]', ans_line, re.DOTALL)
            if exp_match:
                exp_text = exp_match.group(1).strip()

        cursor.execute("SELECT id FROM questions WHERE question = ?", (q_text,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option, explanation, chapter_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (q_text, op_a, op_b, op_c, op_d, correct_opt, exp_text, chapter_name.strip()))
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count

def load_all_github_questions():
    folder_path = "questions"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return

    # Files ko alphabetically/sequentially sort karein (chapter1, chapter2...)
    txt_files = sorted(glob.glob(os.path.join(folder_path, "*.txt")))
    total_new = 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions")
    conn.commit()
    conn.close()

    for file_path in txt_files:
        try:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                new_added = parse_and_insert_txt_content(content, chapter_name=file_name)
                total_new += new_added
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    print(f"📚 Loaded {total_new} questions across all chapters.")
