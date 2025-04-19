import os
import json
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PASSAGE_FILE = "training-data/passages.jsonl"
QUESTION_FILE = "training-data/questions.jsonl"
os.makedirs("training-data", exist_ok=True)

# Load passages
with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
    passages = [json.loads(line.strip()) for line in f if line.strip()]

# Load existing questions to prevent duplication
existing_qids = set()
if os.path.exists(QUESTION_FILE):
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        existing_qids = {json.loads(line)["question_id"] for line in f if line.strip()}

# Helper to call GPT and clean JSON output
def generate_questions_and_tags(passage):
    full_text = "\n\n".join([p["text"] for p in passage["paragraphs"]])
    prompt = f"""
    You are a CARS exam author. Based on the MCAT CARS passage below, generate 5–7 MCAT-style CARS questions in strict JSON format.

    if not passage.get("paragraphs"):
    raise ValueError(f"❌ Passage {passage.get('passage_id')} has no paragraphs.")

    Passage:
    """
    {full_text}
    """

    Return a JSON object with the following fields:

    {{
    "topic": "...",
    "style": "...",
    "structure": "...",
    "questions": [ ... ]
    }}

    ⚠️ Format strictly as raw JSON. Do NOT include markdown or commentary.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert MCAT CARS tutor and exam author."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    raw_output = response.choices[0].message.content.strip()
    raw_output = re.sub(r'^```json\s*|\s*```$', '', raw_output.strip())

    if not raw_output:
        raise ValueError("❌ GPT returned an empty response.")

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as e:
        print("❌ GPT returned invalid JSON:\n", raw_output)
        raise e

# Store output
with open(QUESTION_FILE, "a", encoding="utf-8") as qfile, open(PASSAGE_FILE, "w", encoding="utf-8") as pfile:
    for p in passages:
        if p.get("questions_generated"):
            continue

        print(f"🧠 Generating for {p['passage_id']}...")
        try:
            output = generate_questions_and_tags(p)
            p["topic"] = output.get("topic", "unknown")
            p["style"] = output.get("style", "unknown")
            p["structure"] = output.get("structure", "unknown")
            p["questions_generated"] = True

            questions = output.get("questions", [])
            for i, q in enumerate(questions):
                q["passage_id"] = p["passage_id"]
                q["question_id"] = f"{p['passage_id']}_q{i+1}"
                if q["question_id"] not in existing_qids:
                    if "choices" in q and isinstance(q["choices"], dict) and len(q["choices"]) >= 4:
                        qfile.write(json.dumps(q) + "\n")
        except Exception as e:
            print(f"❌ Error processing {p['passage_id']}: {e}")

    for p in passages:
        pfile.write(json.dumps(p) + "\n")

print("✅ Question generation complete.")
