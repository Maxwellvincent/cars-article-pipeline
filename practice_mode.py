import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env and set up OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths
file_path = os.path.join("data", "comprehension_snippets.json")
output_path = os.path.join("data", "practice_session.json")

# Load comprehension snippets
with open(file_path, "r", encoding="utf-8") as f:
    snippets = json.load(f)

# Use the first snippet for now
snippet = snippets[0]

print("\n🧠 CARS Practice Mode — Strategic Reading Drill")
print("=" * 60)
print(f"\n📘 Title: {snippet['title']}")
print(f"🌐 Source: {snippet['source']}")
print("\n📄 Snippet:\n" + snippet["snippet"])
print("=" * 60)

user_responses = []

# GPT Feedback Function
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt_templates[prompt_type]}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error retrieving feedback: {e}"

# Walk through each sentence
for idx, sentence in enumerate(snippet["sentences"]):
    print(f"\n\n🧩 Sentence {idx+1}: {sentence['text']}")
    print("--------------------------------------------------")

    r_input = input("🗣️ Rephrase: ")
    r_feedback = get_ai_feedback(sentence["text"], "rephrase", r_input)
    print("🤖 Feedback:", r_feedback)

    p_input = input("🎯 Purpose: ")
    p_feedback = get_ai_feedback(sentence["text"], "purpose", p_input)
    print("🤖 Feedback:", p_feedback)

    f_input = input("🔗 Flow: ")
    f_feedback = get_ai_feedback(sentence["text"], "flow", f_input)
    print("🤖 Feedback:", f_feedback)

    i_input = input("💡 Implied meaning: ")
    i_feedback = get_ai_feedback(sentence["text"], "implied", i_input)
    print("🤖 Feedback:", i_feedback)

    user_responses.append({
        "text": sentence["text"],
        "rephrase": r_input,
        "rephrase_feedback": r_feedback,
        "purpose": p_input,
        "purpose_feedback": p_feedback,
        "flow": f_input,
        "flow_feedback": f_feedback,
        "implied": i_input,
        "implied_feedback": i_feedback
    })

# Final summary
print("\n🧠 Final Prompt:")
summary = input(f"{snippet['live_summary_prompt']} ")

# Save session
save = input("\n💾 Save this session for review? (y/n): ").lower()
if save == "y":
    output = {
        "title": snippet["title"],
        "source": snippet["source"],
        "snippet": snippet["snippet"],
        "responses": user_responses,
        "summary": summary
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Session saved to {output_path}")

print("\n🎉 Practice complete! Strong work.")
