import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns



# Load environment
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
PASSAGE_FILE = "training-data/passages.jsonl"
QUESTION_FILE = "training-data/questions.jsonl"

# Step 1: Load and merge questions with passage text
def load_dataset():
    passages = {}
    with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            passages[data["passage_id"]] = data

    records = []
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip blank lines
            try:
                q = json.loads(line)
            except json.JSONDecodeError:
                print("❌ Skipping malformed line in questions.jsonl")
                continue

            passage = passages.get(q["passage_id"])
            if passage:
                linked_para = q.get("linked_paragraph")
                paragraph_text = passage["paragraphs"][linked_para - 1]["text"] if linked_para else ""
                combined_text = f"PASSAGE TITLE: {passage['title']}\nPARAGRAPH: {paragraph_text}\nQUESTION: {q['question_text']}"
                records.append({
                    "input_text": combined_text,
                    "question_type": q["question_type"]
                })
    return pd.DataFrame(records)

# Step 2: Embed text using OpenAI
def embed_text(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print("Embedding error:", e)
        return None

# Step 3: Prepare and embed dataset
def prepare_embeddings(df):
    embeddings = []
    for text in tqdm(df["input_text"], desc="Embedding examples"):
        emb = embed_text(text)
        if emb:
            embeddings.append(emb)
        else:
            embeddings.append([0.0] * 1536)  # fallback vector
    return np.array(embeddings)

# Step 4: Train classifier
def train_classifier(X, y):
    model = LogisticRegression(max_iter=2000)
    model.fit(X, y)
    return model

# Step 5: Evaluate model
def evaluate_model(model, X_test, y_test, le):
    preds = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=le.classes_))

    cm = confusion_matrix(y_test, preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, xticklabels=le.classes_, yticklabels=le.classes_, fmt="d", cmap="Blues")
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.show()

# MAIN
if __name__ == "__main__":
    print("\n🔍 Loading data and preparing training set...")
    df = load_dataset()
    print(f"Loaded {len(df)} examples.")

    print("\n🔢 Generating OpenAI embeddings...")
    X = prepare_embeddings(df)
    le = LabelEncoder()
    y = le.fit_transform(df["question_type"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("\n🧠 Training classifier...")
    model = train_classifier(X_train, y_train)

    evaluate_model(model, X_test, y_test, le)
    print("\n✅ Training complete.")

import joblib
joblib.dump(model, "models/question_type_model.joblib")
joblib.dump(le, "models/label_encoder.joblib")
print("📦 Model and encoder saved to /models/")