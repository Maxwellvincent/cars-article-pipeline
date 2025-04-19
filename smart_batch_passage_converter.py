import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TEXT_FOLDER = "raw-passages"
METADATA_FILE = "raw-metadata.json"
OUTPUT_FILE = "training-data/passages.jsonl"
os.makedirs("training-data", exist_ok=True)

def gpt_annotate_passage(raw_text):
    system_msg = "You are an MCAT CARS editor. Break the passage into paragraphs and annotate each with rhetorical purpose and tone. Estimate overall topic, style, and difficulty (1 to 5)."

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
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("⚠️ GPT error:", e)
        return None

def main():
    print("📚 Starting smart batch passage converter...\n")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata_list = json.load(f)

    processed = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
        for meta in metadata_list:
            pid = meta["passage_id"]
            txt_path = os.path.join(TEXT_FOLDER, f"{pid}.txt")

            if not os.path.exists(txt_path):
                print(f"❌ Missing text file: {pid}.txt")
                continue

            with open(txt_path, "r", encoding="utf-8") as tf:
                raw_text = tf.read().strip()

            print(f"⏳ Processing: {pid} - {meta['title']}")
            result = gpt_annotate_passage(raw_text)

            if not result:
                print(f"❌ GPT failed for: {pid}")
                continue

            final_entry = {
                "passage_id": pid,
                "title": meta["title"],
                "author": meta["author"],
                "journal": meta["journal"],
                "text": raw_text,
                "paragraphs": result["paragraphs"],
                "topic": result["topic"],
                "style": result["style"],
                "estimated_difficulty": result["estimated_difficulty"]
            }

            out.write(json.dumps(final_entry) + "\n")
            print(f"✅ Saved: {pid} (difficulty {result['estimated_difficulty']})\n")
            processed += 1

    print(f"\n🎉 Finished! {processed} passage(s) written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
