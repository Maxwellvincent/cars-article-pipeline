import os
import json
import glob
from pathlib import Path

RAW_DIRS = ["raw-passages", "data"]
TARGET_FILE = "training-data/passages.jsonl"
PROCESSED_IDS = set()

# Load existing passage IDs to avoid duplicates and get max ID
def load_existing_passage_ids():
    if not os.path.exists(TARGET_FILE):
        return set(), 0
    existing_ids = set()
    max_num = 0
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            pid = data.get("passage_id")
            if pid:
                existing_ids.add(pid)
                if pid[0] == "p" and pid[1:].isdigit():
                    max_num = max(max_num, int(pid[1:]))
    return existing_ids, max_num

# Load passage entries from .json files in each source folder
def collect_passages():
    passages = []
    for folder in RAW_DIRS:
        source_label = folder.replace("-passages", "").replace("_", "-")
        files = glob.glob(os.path.join(folder, "*.json"))
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    entries = data if isinstance(data, list) else [data]
                    for p in entries:
                        p["source"] = source_label
                        p["processed_by"] = "gpt-4" if "gpt" in source_label else "manual"
                        p["generated_by"] = "auto" if "gpt" in source_label else "user"
                        passages.append(p)
                except Exception as e:
                    print(f"❌ Error loading {file_path}: {e}")
    return passages

# Write only new passages to training-data/passages.jsonl
def write_passages(new_passages):
    with open(TARGET_FILE, "a", encoding="utf-8") as f:
        for entry in new_passages:
            f.write(json.dumps(entry) + "\n")

# Ingest pipeline
if __name__ == "__main__":
    print("🔍 Scanning for new passages...")
    Path("training-data").mkdir(exist_ok=True)
    PROCESSED_IDS, MAX_ID = load_existing_passage_ids()
    all_passages = collect_passages()

    new_passages = []
    for i, p in enumerate(all_passages):
        if not p.get("passage_id"):
            MAX_ID += 1
            p["passage_id"] = f"p{MAX_ID:03}"
        if p["passage_id"] not in PROCESSED_IDS:
            new_passages.append(p)

    if new_passages:
        print(f"✅ Found {len(new_passages)} new passage(s). Writing to {TARGET_FILE}...")
        write_passages(new_passages)
        print("✨ Ingestion complete.")
    else:
        print("📭 No new passages found.")
