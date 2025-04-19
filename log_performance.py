import json
import os
from datetime import datetime

USER_PROFILE_PATH = "user/user_profile.json"
USER_LOG_PATH = "user/user_logs.jsonl"
os.makedirs("user", exist_ok=True)

# Initialize profile if it doesn't exist
def initialize_profile():
    if not os.path.exists(USER_PROFILE_PATH):
        profile = {
            "question_stats": {},
            "difficulty_stats": {str(i): {"seen": 0, "correct": 0} for i in range(1, 11)},
            "recent_activity": []
        }
        with open(USER_PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=2)

# Log one question result
def log_question_performance(question_id, question_type, difficulty, was_correct):
    initialize_profile()

    # Load existing profile
    with open(USER_PROFILE_PATH, "r") as f:
        profile = json.load(f)

    # Update question stats
    q_stats = profile["question_stats"].setdefault(question_type, {"attempts": 0, "correct": 0})
    q_stats["attempts"] += 1
    if was_correct:
        q_stats["correct"] += 1

    # Update difficulty stats
    diff_key = str(difficulty)
    if diff_key not in profile["difficulty_stats"]:
        profile["difficulty_stats"][diff_key] = {"seen": 0, "correct": 0}
    profile["difficulty_stats"][diff_key]["seen"] += 1
    if was_correct:
        profile["difficulty_stats"][diff_key]["correct"] += 1

    # Add to recent activity
    profile["recent_activity"].insert(0, {
        "question_id": question_id,
        "question_type": question_type,
        "difficulty": difficulty,
        "was_correct": was_correct,
        "timestamp": datetime.now().isoformat()
    })
    profile["recent_activity"] = profile["recent_activity"][:100]  # keep last 100

    # Save profile
    with open(USER_PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)

    # Save full log line
    log_entry = {
        "question_id": question_id,
        "question_type": question_type,
        "difficulty": difficulty,
        "was_correct": was_correct,
        "timestamp": datetime.now().isoformat()
    }
    with open(USER_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"✅ Logged result for {question_id} ({'correct' if was_correct else 'wrong'})")

# Example CLI use
if __name__ == "__main__":
    qid = input("Question ID: ")
    qtype = input("Question type: ")
    difficulty = int(input("Passage difficulty (1-10): "))
    was_correct = input("Was correct? (y/n): ").strip().lower() == "y"
    log_question_performance(qid, qtype, difficulty, was_correct)
