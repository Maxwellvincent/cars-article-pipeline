import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from predict_question_type import predict_question_type


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUESTION_FILE = "training-data/questions.jsonl"
PASSAGE_FILE = "training-data/passages.jsonl"
TEMP_FILE = "training-data/questions_temp.jsonl"

def load_passages():
    passages = {}
    with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line.strip())
            passages[entry["passage_id"]] = entry
    return passages

def load_questions():
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f]

def save_questions(questions):
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")
    os.replace(TEMP_FILE, QUESTION_FILE)

def list_questions_by_passage(questions, pid):
    return [q for q in questions if q["passage_id"] == pid]

def display_question(q, passage=None):
    print(f"\n\U0001F9E0 {q['question_id']}")
    print(f"❓ {q['question_text']}")
    for label, text in q["choices"].items():
        print(f"  {label}. {text}")
    print(f"✅ Correct: {q['correct_answer']}")
    print(f"📌 Type: {q['question_type']}")
    print("📖 Explanations:")
    for k, v in q["explanations"].items():
        print(f"  - {k}: {v}")

    if passage and "linked_paragraph" in q and isinstance(q["linked_paragraph"], int):
        idx = q["linked_paragraph"] - 1
        if 0 <= idx < len(passage["paragraphs"]):
            print(f"\n🔍 Highlighted Paragraph (Linked to Q):")
            print(f"   📌 Purpose: {passage['paragraphs'][idx]['rhetorical_purpose']} | 🗭 Tone: {passage['paragraphs'][idx]['tone']}")
            print(f"\n{passage['paragraphs'][idx]['text']}")

def suggest_paragraph_from_gpt(passage, question_text):
    numbered = "\n".join(
        [f"{i+1}. {p['text']}" for i, p in enumerate(passage["paragraphs"])]
    )

    prompt = f"""
Given the question below and the following numbered paragraphs from a passage, identify which paragraph is most relevant to answering the question.

Return only the number (1-based).

QUESTION:
{question_text}

PARAGRAPHS:
{numbered}

Response format:
{{ "paragraph_number": 3 }}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a CARS tutor assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        parsed = json.loads(response.choices[0].message.content)
        return parsed.get("paragraph_number")
    except Exception as e:
        print("\u274c GPT paragraph suggestion error:", e)
        return None

def edit_question(q, passage):
    print("\n✏️ Editing question...")
    q["question_text"] = input("New question text (leave blank to keep): ") or q["question_text"]
    for label in q["choices"]:
        c = input(f"{label}. New choice (blank = keep): ")
        if c:
            q["choices"][label] = c
    q["correct_answer"] = input("New correct answer (A-D, blank = keep): ").upper() or q["correct_answer"]
    q["question_type"] = input("New question type (blank = keep): ") or q["question_type"]
    for label in q["explanations"]:
        e = input(f"New explanation for {label} (blank = keep): ")
        if e:
            q["explanations"][label] = e

    auto_link = input("\U0001F517 Auto-suggest linked paragraph using GPT? (y/n): ").lower()
    if auto_link == "y":
        paragraph_number = suggest_paragraph_from_gpt(passage, q["question_text"])
        print(f"🤖 GPT suggests Paragraph {paragraph_number} as most relevant.")
    else:
        paragraph_number = input("Manual paragraph number link (1, 2, etc.): ")

    q["linked_paragraph"] = int(paragraph_number) if str(paragraph_number).isdigit() else None
    print("✅ Updated.")

def delete_question(questions, qid):
    return [q for q in questions if q["question_id"] != qid]

def create_question(passage_id, all_questions, passage):
    question_text = input("\n❓ Question text:\n")

    auto_type = input("🤖 Auto-predict question type using ML model? (y/n): ").lower()

    if auto_type == "y":
        predicted_type, probs = predict_question_type(
            passage_title=passage["title"],
            paragraph_text=passage["paragraphs"][0]["text"],  # you can swap this with linked_para later
            question_text=question_text
        )
        print(f"✅ Predicted Type: {predicted_type}")
        print("📊 Confidence:")
        for k, v in sorted(probs.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v:.2f}")
        qtype = predicted_type
    else:
        qtype = input("📎 Enter question type manually: ")
    
    existing_ids = [q["question_id"] for q in all_questions if q["passage_id"] == passage_id]
    qid = f"{passage_id}_q{len(existing_ids) + 1}"

    auto_link = input("\U0001F517 Auto-suggest linked paragraph using GPT? (y/n): ").lower()
    if auto_link == "y":
        paragraph_number = suggest_paragraph_from_gpt(passage, question_text)
        print(f"🤖 GPT suggests Paragraph {paragraph_number} as most relevant.")
    else:
        paragraph_number = input("Manual paragraph number link (1, 2, etc.): ")

    return {
        "passage_id": passage_id,
        "question_id": qid,
        "question_text": question_text,
        "choices": choices,
        "correct_answer": correct,
        "question_type": qtype,
        "explanations": explanations,
        "trap_types": {},
        "linked_paragraph": int(paragraph_number) if str(paragraph_number).isdigit() else None,
        "difficulty_rating": 3
    }

def main():
    questions = load_questions()
    passages = load_passages()

    print(f"\n📊 Total questions loaded: {len(questions)}")
    passage_id = input("📘 Enter passage ID to manage: ").strip()

    if passage_id not in passages:
        print(f"⚠️ No passage found for ID: {passage_id}")
        return

    passage = passages[passage_id]
    print(f"\n📝 Full Passage for {passage_id}: {passage['title']}")
    print(f"📚 Source: {passage['journal']} | ✍️ {passage['author']}\n")

    for idx, para in enumerate(passage["paragraphs"]):
        print(f"🔹 Paragraph {idx + 1}:")
        print(f"{para['text']}\n")
        print(f"   📌 Purpose: {para['rhetorical_purpose']}  |  🧭 Tone: {para['tone']}\n")
        print("-" * 60)

    filtered = list_questions_by_passage(questions, passage_id)
    print(f"\n📎 Found {len(filtered)} question(s) for this passage.")

    while True:
        print("\n🔧 OPTIONS:")
        print("1. List all questions")
        print("2. Edit a question")
        print("3. Delete a question")
        print("4. Add a new question")
        print("5. Save & Exit")
        print("6. Exit without saving")

        choice = input("\nChoose an option (1-6): ").strip()

        if choice == "1":
            for q in filtered:
                display_question(q, passage)

        elif choice == "2":
            qid = input("Enter question ID to edit: ").strip()
            q = next((q for q in filtered if q["question_id"] == qid), None)
            if q:
                edit_question(q, passage)
            else:
                print("❌ Question ID not found.")

        elif choice == "3":
            qid = input("Enter question ID to delete: ").strip()
            before = len(filtered)
            filtered = delete_question(filtered, qid)
            if len(filtered) < before:
                print("✅ Deleted.")
            else:
                print("❌ Question ID not found.")

        elif choice == "4":
            new_q = create_question(passage_id, questions, passage)
            filtered.append(new_q)
            print("✅ Question added.")

        elif choice == "5":
            rest = [q for q in questions if q["passage_id"] != passage_id]
            save_questions(rest + filtered)
            print("💾 Saved. Exiting.")
            break

        elif choice == "6":
            print("❌ Exit without saving.")
            break

        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
