import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
input_path = os.path.join("data", "articles.json")
output_path = os.path.join("data", "refined_passages.json")

# Load articles
with open(input_path, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Split into 400–600 word chunks
def chunk_paragraphs(paragraphs, min_words=400, max_words=600):
    chunks, current_chunk, count = [], [], 0
    for para in paragraphs:
        wc = len(para["text"].split())
        if count + wc <= max_words:
            current_chunk.append(para["text"])
            count += wc
        else:
            if count >= min_words:
                chunks.append(" ".join(current_chunk))
            current_chunk = [para["text"]]
            count = wc
    if current_chunk and count >= min_words:
        chunks.append(" ".join(current_chunk))
    return chunks

# GPT prompt to reframe and annotate
def refine_passage(raw_text):
    prompt = f"""
You are an MCAT CARS passage generator.

Given this text, reframe it as a standalone MCAT-style passage (400–600 words) suitable for testing reading comprehension. Maintain complex reasoning and abstract tone. Then, annotate the rhetorical purpose of each paragraph (e.g., thesis, support, counterpoint, elaboration, shift, conclusion).

Output format:
PASSAGE:
<reframed passage here>

ANNOTATIONS:
Paragraph 1: <purpose>
Paragraph 2: <purpose>
...
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a high-level academic editor with expertise in exam prep."},
                {"role": "user", "content": prompt.replace("<raw>", raw_text)}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT error: {e}"

# Process articles
refined = []

for article in articles:
    paragraphs = article.get("paragraphs", [])
    chunks = chunk_paragraphs(paragraphs)

    for chunk in chunks:
        refined_output = refine_passage(chunk)
        refined.append({
            "title": article.get("title"),
            "source": article.get("url"),
            "raw_chunk": chunk,
            "refined_passage": refined_output
        })

# Save output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(refined, f, indent=2)

print(f"✅ Refined passages saved to {output_path}")
