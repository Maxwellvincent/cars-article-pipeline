import json
import os

QUESTION_FILE = "training-data/questions.jsonl"
TEMP_FILE = "training-data/questions_temp.jsonl"

def load_questions():
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f]

def detect_duplicates(questions):
    seen = set()
    duplicates = []
    for q in questions:
        qt = q["question_text"].strip()
        if qt in seen:
            duplicates.append(q)
        else:
            seen.add(qt)
    return duplicates

def review_questions(questions):
    for idx, q in enumerate(questions):
        print(f"\n🧠 Question {idx + 1}/{len(questions)} — ID: {q['question_id']}")
        print(f"📘 Passage: {q['passage_id']}")
        print(f"❓ {q['question_text']}")
        print("Choices:")
        for label, choice in q["choices"].items():
            print(f"  {label}. {choice}")
        print(f"✅ Correct: {q['correct_answer']}")
        print(f"📎 Type: {q['question_type']}")
        print(f"📖 Explanations:")
        for k, v in q["explanations"].items():
            print(f"  - {k}: {v}")

        edit = input("\n✏️ Edit this question? (y/n): ").strip().lower()
        if edit == "y":
            q["question_text"] = input("New question text (leave blank to keep): ") or q["question_text"]
            for label in q["choices"]:
                new_c = input(f"{label}. New choice (blank = keep): ")
                if new_c:
                    q["choices"][label] = new_c
            q["correct_answer"] = input("New correct answer (A/B/C/D, blank = keep): ").upper() or q["correct_answer"]
            q["question_type"] = input("New question type (blank = keep): ") or q["question_type"]
            for label in q["explanations"]:
                new_exp = input(f"Explain {label} (blank = keep): ")
                if new_exp:
                    q["explanations"][label] = new_exp
            print("✅ Question updated.")

    return questions

def save_questions(questions):
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")
    os.replace(TEMP_FILE, QUESTION_FILE)

def main():
    print("\n🔎 Loading questions...")
    questions = load_questions()
    print(f"📊 Loaded {len(questions)} questions.")

    duplicates = detect_duplicates(questions)
    if duplicates:
        print(f"\n⚠️ Found {len(duplicates)} duplicate question(s) based on identical text.")
        for d in duplicates:
            print(f"  - {d['question_id']}: {d['question_text'][:100]}...")
    else:
        print("✅ No duplicate questions detected.")

    do_review = input("\n🧪 Do you want to review/edit questions now? (y/n): ").strip().lower()
    if do_review == "y":
        questions = review_questions(questions)
        save_questions(questions)
        print("✅ All updates saved.")

if __name__ == "__main__":
    main()
