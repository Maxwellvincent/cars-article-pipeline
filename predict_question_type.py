import os
import json
import joblib
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI key and initialize
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load saved model and label encoder
MODEL_PATH = "models/question_type_model.joblib"
ENCODER_PATH = "models/label_encoder.joblib"

model = joblib.load(MODEL_PATH)
le = joblib.load(ENCODER_PATH)

# Embed text using OpenAI
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

# Predict question type given a passage + question
def predict_question_type(passage_title, paragraph_text, question_text):
    combined_input = f"PASSAGE TITLE: {passage_title}\nPARAGRAPH: {paragraph_text}\nQUESTION: {question_text}"
    embedding = embed_text(combined_input)
    if not embedding:
        return None, None

    pred_label_idx = model.predict([embedding])[0]
    proba = model.predict_proba([embedding])[0]
    class_probs = dict(zip(le.classes_, proba))
    return le.inverse_transform([pred_label_idx])[0], class_probs

# CLI entry for quick testing
if __name__ == "__main__":
    print("\n🧪 Predict Question Type using trained model")
    title = input("Passage title: ")
    paragraph = input("Relevant paragraph: ")
    question = input("Question text: ")

    qtype, probs = predict_question_type(title, paragraph, question)
    if qtype:
        print(f"\n✅ Predicted Question Type: {qtype}")
        print("\n📊 Probabilities:")
        for k, v in sorted(probs.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v:.3f}")
    else:
        print("❌ Prediction failed.")
