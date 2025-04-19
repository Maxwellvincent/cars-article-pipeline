import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PASSAGE_FILE = "training-data/passages.jsonl"
QUESTION_FILE = "training-data/questions.jsonl"
os.makedirs("training-data", exist_ok=True)

def load_passages():
    passages = {}
    with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            passages[data["passage_id"]] = data
    return passages

def get_gpt_question_analysis(passage_text, question, choices, correct_answer):
    formatted_choices = "\n".join([f"{k}. {v}" for k, v in choices.items()])
    prompt = f"""
You are an MCAT CARS question classifier.

Given the passage and question below, do two things:
1. Identify the **question type** (main idea, inference, function, tone, logic, detail).
2. Label each incorrect choice with its **trap type** (out of scope, distortion, extreme, half-true, neutral, etc.).

PASSAGE:
\"\"\"
{passage_text}
\"\"\"

QUESTION:
{question}

CHOICES:
{formatted_choices}

CORRECT ANSWER: {correct_answer}

Return this format:
{{
  "question_type": "main idea",
  "trap_types": {{
    "A": "distortion",
    "C": "out of scope",
    "D": "extreme"
  }}
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a CARS tutor and MCAT question analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("❌ GPT error:", e)
        return None

def main():
    print("🧠 CARS Question Converter + Reasoning Capture")
    passages = load_passages()

    passage_id = input("📘 Enter passage ID (e.g., p001): ").strip()

    if passage_id not in passages:
        print("❌ Invalid passage ID.")
        return

    passage_text = passages[passage_id]["text"]

    question_text = input("\n❓ Enter question text:\n")

    choices = {}
    explanations = {}

    for label in ["A", "B", "C", "D"]:
        choices[label] = input(f"{label}: ")
        explanations[label] = input(f"🧠 Explain why {label} is right or wrong:\n")

    correct = input("✅ Enter correct answer (A/B/C/D): ").strip().upper()

    if correct not in choices:
        print("❌ Invalid correct choice.")
        return

    print("\n⏳ Sending to GPT for classification...")
    analysis = get_gpt_question_analysis(passage_text, question_text, choices, correct)

    if not analysis:
        print("⚠️ Skipping question.")
        return

    question_entry = {
        "passage_id": passage_id,
        "question_id": f"{passage_id}_q{len(os.listdir('training-data'))}",
        "question_text": question_text,
        "question_type": analysis["question_type"],
        "correct_answer": correct,
        "choices": choices,
        "trap_types": analysis["trap_types"],
        "explanations": explanations,
        "difficulty_rating": 3  # optional
    }

    with open(QUESTION_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(question_entry) + "\n")

    print("✅ Question saved to questions.jsonl")
    print(f"🔍 GPT classified as: {analysis['question_type']}")
    print("📌 Trap types:")
    for k, v in analysis["trap_types"].items():
        print(f"  - {k}: {v}")
    print("📖 Explanations captured for all choices.")

if __name__ == "__main__":
    main()
