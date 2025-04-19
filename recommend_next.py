import json
import os
from collections import defaultdict

USER_PROFILE_PATH = "user/user_profile.json"
PASSAGE_FILE = "training-data/passages.jsonl"

def load_user_profile():
    if not os.path.exists(USER_PROFILE_PATH):
        return None
    with open(USER_PROFILE_PATH, "r") as f:
        return json.load(f)

def load_passages():
    passages = []
    if not os.path.exists(PASSAGE_FILE):
        return passages
    with open(PASSAGE_FILE, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            passages.append(data)
    return passages

def identify_weak_areas(profile):
    weaknesses = []
    for qtype, stats in profile.get("question_stats", {}).items():
        if stats["attempts"] >= 3:
            accuracy = stats["correct"] / stats["attempts"]
            if accuracy < 0.7:
                weaknesses.append((qtype, accuracy))
    weaknesses.sort(key=lambda x: x[1])  # sort by lowest accuracy
    return [w[0] for w in weaknesses]

def recommend_passages(profile, passages):
    weak_types = identify_weak_areas(profile)
    recommended = []

    for p in passages:
        qtypes_in_passage = set()
        for para in p.get("paragraphs", []):
            if any(weak in para.get("rhetorical_purpose", "") for weak in weak_types):
                qtypes_in_passage.add(para.get("rhetorical_purpose"))

        if qtypes_in_passage:
            recommended.append((p, len(qtypes_in_passage)))

    recommended.sort(key=lambda x: (-x[1], x[0].get("estimated_difficulty", 5)))
    return [rec[0] for rec in recommended[:5]]

def recommend_next():
    profile = load_user_profile()
    if not profile:
        print("⚠️ No user profile found.")
        return

    passages = load_passages()
    if not passages:
        print("⚠️ No passages available.")
        return

    recommendations = recommend_passages(profile, passages)
    print("\n🎯 Recommended Passages:")
    for p in recommendations:
        print(f"- {p['passage_id']}: {p['title']} | Difficulty: {p['estimated_difficulty']} | Source: {p['journal']}")

if __name__ == "__main__":
    recommend_next()
