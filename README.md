# MCAT CARS Comprehension Trainer 🧠📚

A powerful, AI-assisted training app designed to help students master the **Critical Analysis and Reasoning Skills (CARS)** section of the MCAT.

Built for students who struggle with reading comprehension, this app uses OpenAI’s GPT-3.5-turbo model to provide feedback, generate MCAT-style passages, and reinforce strategic reading through active practice.

---

## 🚀 Features

- ✅ Converts real articles into **MCAT-style CARS passages**
- 🧱 Applies a **9-step Strategic Reading Framework** per sentence
- 🤖 Provides **AI feedback** on rephrasing, rhetorical purpose, flow, and implied meaning
- 🧠 Tracks comprehension sessions and stores them for later review
- ✂️ Filters full articles into **500-word reasoning-dense chunks**
- 🔁 Easily extendable to include MCAT-style question generation and leveling systems

---

## 🛠 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/cars-article-pipeline.git
cd cars-article-pipeline
2. Install Requirements
bash
Copy
Edit
pip install -r requirements.txt
3. Add Your OpenAI API Key
Create a .env file in the root:

env
Copy
Edit
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
🧪 How to Use
🔄 Step 1: Refine Raw Articles into CARS Passages
bash
Copy
Edit
python article_refiner.py
This will create data/refined_passages.json — a set of GPT-enhanced MCAT-style passages with paragraph-level annotations.

📘 Step 2: Practice Reading Comprehension
bash
Copy
Edit
python practice_mode_refined.py
This runs a structured sentence-by-sentence reading session, asking you to:

Rephrase the sentence

Explain its rhetorical purpose

Describe how it connects to the previous idea

Identify implied meaning

OpenAI then gives you constructive feedback and a rating.

📁 File Structure
bash
Copy
Edit
cars-article-pipeline/
├── article_refiner.py            # Converts articles into MCAT-style passages
├── practice_mode_refined.py      # Comprehension training interface
├── data/
│   ├── articles.json
│   ├── refined_passages.json
│   └── practice_refined.json
├── requirements.txt
├── .env
└── README.md
🧠 Roadmap
 Passage rotation + difficulty scaling

 Power level tracker based on speed, depth, and GPT feedback

 MCAT-style question generator (Main Idea, Inference, Function)

 Flashcard and Anki export options

 Web-based interface (Flask/React or Streamlit)

 Data dashboard for review and progress tracking

📜 License
MIT License — free to use, modify, and expand with attribution.

💬 Author
Built by @Maxwellvincent

yaml
Copy
Edit

---

## ✅ Then Commit and Push

```bash
git add README.md
git commit -m "Add full project README documentation"
git push origin main