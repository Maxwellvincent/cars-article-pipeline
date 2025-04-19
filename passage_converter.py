import json
import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Output path
os.makedirs("training-data", exist_ok=True)
output_path = os.path.join("training-data", "passages.jsonl")

# Prompt function to call GPT
def analyze_passage_with_gpt(raw_text):
    system_msg = "You are an MCAT CARS editor. Your job is to break a passage into paragraphs, and annotate each with rhetorical purpose and tone. Also estimate overall topic, style, and difficulty from 1 (easy) to 5 (very hard)."

    user_prompt = f"""
Text:
{raw_text}

Return JSON like:
{{
  "paragraphs": [
    {{
      "text": "...",
      "rhetorical_purpose": "thesis | support | counterpoint | shift | conclusion | example | elaboration",
      "tone": "neutral | critical | skeptical | analytical | optimistic | defensive"
    }},
    ...
  ],
  "topic": "...",
  "style": "...",
  "estimated_difficulty": 1-5
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        print("⚠️ GPT error:", e)
        return None

# Main interactive loop
def main():
    print("\n🧠 MCAT Passage Formatter with GPT Co-Pilot")
    raw = input("\nPaste your raw passage:\n\n")
    
    print("\n⏳ Sending to GPT for analysis...")
    result = analyze_passage_with_gpt(raw)

    if result is None:
        print("❌ Failed to process passage.")
        return

    entry = {
        "passage_id": str(uuid.uuid4())[:8],
        "source": "manual-entry",
        "text": raw,
        "paragraphs": result["paragraphs"],
        "topic": result["topic"],
        "style": result["style"],
        "estimated_difficulty": result["estimated_difficulty"]
    }

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"\n✅ Passage saved to {output_path}")
    print(f"📘 Topic: {entry['topic']}, Style: {entry['style']}, Difficulty: {entry['estimated_difficulty']}")

if __name__ == "__main__":
    main()
