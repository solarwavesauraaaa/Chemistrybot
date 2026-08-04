# parser.py

def parse_txt_questions(file_path):
    """Txt file ko parse karke question objects ki list return karta hai"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    parsed_questions = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        
        q_text, opt_a, opt_b, opt_c, opt_d = "", "", "", "", ""
        ans_str, exp_text = "", ""

        for line in lines:
            if line.startswith("Q:"):
                q_text = line[2:].strip()
            elif line.startswith("A)"):
                opt_a = line[2:].strip()
            elif line.startswith("B)"):
                opt_b = line[2:].strip()
            elif line.startswith("C)"):
                opt_c = line[2:].strip()
            elif line.startswith("D)"):
                opt_d = line[2:].strip()
            elif line.startswith("Answer:"):
                # Answer ka alphabet (A/B/C/D) nikalna
                parts = line.split("Answer:")
                if parts[1].strip():
                    ans_str = parts[1].strip()[0].upper()
                
                # Brackets [] ke andar se explanation nikalna
                if "[" in line and "]" in line:
                    exp_text = line.split("[")[1].split("]")[0].strip()

        ans_map = {"A": 0, "B": 1, "C": 2, "D": 3}
        # Agar sawal aur saare options mil gaye hain, tabhi DB me add karega
        if q_text and opt_a and opt_b and opt_c and opt_d and ans_str in ans_map:
            parsed_questions.append({
                "question": q_text,
                "options": [opt_a, opt_b, opt_c, opt_d],
                "correct_id": ans_map[ans_str],
                "explanation": exp_text
            })

    return parsed_questions