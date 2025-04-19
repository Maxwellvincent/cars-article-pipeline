import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_FOLDER = "raw-passages"
OUTPUT_FILE = "training-data/passages.jsonl"
os.makedirs("training-data", exist_ok=True)

# GPT function to annotate passage text
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

# Batch processing loop
def main():
    print("📚 Starting batch processing of passages...\n")

    files = [f for f in os.listdir(RAW_FOLDER) if f.endswith(".json")]
    processed = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as output_file:
        for filename in files:
            filepath = os.path.join(RAW_FOLDER, filename)
            print(f"🔍 Trying to load: {filepath}")

            with open(filepath, "r", encoding="utf-8") as f:
                passage_data = json.load(f)

            print(f"⏳ Processing {filename}...")

            gpt_result = gpt_annotate_passage(passage_data["text"])
            if not gpt_result:
                print(f"❌ Failed to process {filename}\n")
                continue

            # Combine GPT result with original metadata
            final_data = {
                "passage_id": passage_data.get("passage_id", filename.replace(".json", "")),
                "title": passage_data.get("title", ""),
                "author": passage_data.get("author", ""),
                "journal": passage_data.get("journal", ""),
                "text": passage_data["text"],
                "paragraphs": gpt_result["paragraphs"],
                "topic": gpt_result["topic"],
                "style": gpt_result["style"],
                "estimated_difficulty": gpt_result["estimated_difficulty"]
            }

            output_file.write(json.dumps(final_data) + "\n")
            print(f"✅ Saved: {final_data['passage_id']} — difficulty {final_data['estimated_difficulty']}\n")
            processed += 1

    print(f"\n🎉 Finished! {processed} passage(s) processed and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
