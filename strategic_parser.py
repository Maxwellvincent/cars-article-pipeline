import json
import os
import re

# Paths
input_path = os.path.join("data", "articles.json")
output_path = os.path.join("data", "comprehension_snippets.json")

# Load articles
with open(input_path, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Keyword groups
keywords = {
    "contrast": ['however', 'but', 'although', 'yet', 'nevertheless', 'rather', 'in contrast', 'on the other hand', 'otherwise', 'nevertheless', 'wheras', 'while', 'different', 'unlike'],
    "similarity": ['and', 'also', 'moreover', 'futhermore', 'like', 'same', 'similar','that is', 'in other words', 'for example', 'for instance', 'take the case of', 'including', 'such as', 'in addition', 'at the same time', 'as well as', 'equally', 'this','that', 'these', 'those', ';',':', '-'],
    "opposition": ['not', 'never', 'none', 'on the contrary', 'as opposed to', 'versus', 'otherwise'],
    "emphasis": ['indeed', 'in fact', 'clearly', 'must', 'above all'],
    "moderating": ['can', 'could', 'may', 'might', 'possibly', 'probably', 'sometimes', 'on occasion', 'often', 'tends to', 'here', 'now', 'in this case', 'in some sense'],
    "logic": ['because', 'since', 'therefore', 'as a result', 'due to']
}

# Function: determine clause type
def identify_clause_type(text):
    if any(w in text.lower() for w in ["because", "although", "if", "while", "since"]):
        return "dependent"
    return "independent"

# Function: create MCAT-like passages (500 words)
def chunk_passage(paragraphs, max_words=500):
    chunks = []
    current_chunk = []
    current_count = 0
    for para in paragraphs:
        word_count = len(para.split())
        if current_count + word_count <= max_words:
            current_chunk.append(para)
            current_count += word_count
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [para]
            current_count = word_count
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# Output container
comprehension_snippets = []

# Process all articles
for article in articles:
    paragraphs = [p["text"] for p in article.get("paragraphs", []) if "text" in p]
    snippets = chunk_passage(paragraphs)

    for snippet in snippets:
        sentences = re.split(r'(?<=[.!?])\s+', snippet.strip())
        parsed = []

        for sentence in sentences:
            if not sentence:
                continue
            subject = sentence.split()[0]
            verb = next((word for word in sentence.split() if word.endswith('s') or word in ['is', 'are', 'was', 'were']), "")
            clause_type = identify_clause_type(sentence)
            found_keywords = [k for k, group in keywords.items() if any(w in sentence.lower() for w in group)]
            parsed.append({
                "text": sentence,
                "subject": subject,
                "verb": verb,
                "clause_type": clause_type,
                "keywords": found_keywords,
                "rhetorical_purpose": "",
                "prompts": {
                    "rephrase": "Can you rephrase this sentence in your own words?",
                    "purpose": "What is the rhetorical role of this sentence (support, shift, counterpoint)?",
                    "flow": "How does this sentence connect to the previous one?",
                    "implied": "What is implied but not directly stated in this sentence?"
                }
})

        comprehension_snippets.append({
            "title": article.get("title"),
            "source": article.get("url"),
            "snippet": snippet,
            "sentences": parsed,
            "live_summary_prompt": "Summarize the passage so far in 2–3 sentences."
        })

# Save file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(comprehension_snippets, f, indent=2)

print("✅ comprehension_snippets.json saved.")
