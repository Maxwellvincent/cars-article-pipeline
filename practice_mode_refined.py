import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load your OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File path to refined passages
refined_path = os.path.join("data", "refined_passages.json")
with open(refined_path, "r", encoding="utf-8") as f:
    refined_data = json.load(f)

# Load the first refined passage
refined = refined_data[0]
passage_text = refined["refined_passage"]

print("\n🧠 CARS Refined Practice Mode")
print("=" * 60)
print(f"📘 Title: {refined['title']}")
print(f"🌐 Source: {refined['source']}\n")
print("📄 Full Passage:\n")
print(passage_text.split("ANNOTATIONS:")[0].strip())
print("=" * 60)

# Extract only the passage text (remove annotations)
raw_passage = passage_text.split("ANNOTATIONS:")[0].strip()
paragraphs = raw_passage.split("\n\n")
sentences = [s for p in paragraphs for s in re.split(r'(?<=[.!?])\s+', p.strip()) if s]

# GPT Feedback Function (v1.0 format, gpt-3.5-turbo)
def get_ai_feedback(sentence, prompt_type, user_response):
    system_msg = (
        "You are an MCAT CARS tutor. Your goal is to evaluate a student's response to a comprehension prompt. "
        "Be brief but constructive. Rate the response from 1 to 5 and explain why."
    )

    prompt_templates = {
        "rephrase": f"""Evaluate the student's rephrasing of this sentence:

Sentence: "{sentence}"
Student rephrased it as: "{user_response}"

Provide feedback and rate from 1 to 5.
""",
        "purpose": f"""Evaluate the student's analysis of the rhetorical purpose of this sentence:

Sentence: "{sentence}"
Student's response: "{user_response}"

Is it accurate? Explain and rate from 1 to 5.
""",
        "flow": f"""Evaluate how well the student explained the connection between this sentence and the previous one:

Sentence: "{sentence}"
Student's response: "{user_response}"

Give a short critique and a rating from 1 to 5.
""",
        "implied": f"""Evaluate the student's understanding of the implied meaning in this sentence:

Sentence: "{sentence}"
Student's response: "{user_response}"

Give feedback and rate from 1 to 5.
"""
    }

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # ✅ Updated model
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt_templates[prompt_type]}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error retrieving feedback: {e}"

# Begin sentence-by-sentence comprehension drill
user_responses = []
for i, sentence in enumerate(sentences):
    print(f"\n\n🧩 Sentence {i+1}: {sentence}")
    print("--------------------------------------------------")

    r_input = input("🗣️ Rephrase: ")
    r_feedback = get_ai_feedback(sentence, "rephrase", r_input)
    print("🤖 Feedback:", r_feedback)

    p_input = input("🎯 Purpose: ")
    p_feedback = get_ai_feedback(sentence, "purpose", p_input)
    print("🤖 Feedback:", p_feedback)

    f_input = input("🔗 Flow: ")
    f_feedback = get_ai_feedback(sentence, "flow", f_input)
    print("🤖 Feedback:", f_feedback)

    i_input = input("💡 Implied meaning: ")
    i_feedback = get_ai_feedback(sentence, "implied", i_input)
    print("🤖 Feedback:", i_feedback)

    user_responses.append({
        "text": sentence,
        "rephrase": r_input,
        "rephrase_feedback": r_feedback,
        "purpose": p_input,
        "purpose_feedback": p_feedback,
        "flow": f_input,
        "flow_feedback": f_feedback,
        "implied": i_input,
        "implied_feedback": i_feedback
    })

# Optional summary
summary = input("\n🧠 Final Summary (2–3 sentence recap of passage): ")

# Save session
save = input("\n💾 Save this session as `practice_refined.json`? (y/n): ").lower()
if save == "y":
    with open("data/practice_refined.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": refined["title"],
            "source": refined["source"],
            "responses": user_responses,
            "summary": summary
        }, f, indent=2)
    print("✅ Saved to data/practice_refined.json")

print("\n🎉 Practice complete!")
