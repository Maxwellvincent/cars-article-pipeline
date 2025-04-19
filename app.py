from flask import Flask, redirect, url_for, session, request, render_template
from authlib.integrations.flask_client import OAuth
import os, json
from pathlib import Path
from log_performance import log_question_performance
import time


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")  # change this in production

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


USER_DIR = Path("user_profiles")
USER_DIR.mkdir(exist_ok=True)

@app.route("/")
def index():
    user = session.get('user')
    if user:
        return redirect(url_for('dashboard'))
    return "<a href='/login'>Login with Google</a>"


@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    user_id = user["sub"]
    profile_path = USER_DIR / user_id / "user_profile.json"
    if not profile_path.exists():
        return "No profile data yet."

    with open(profile_path, "r") as f:
        profile = json.load(f)

    # You can later add subject-specific stats
    subjects = [
        {"id": "mcat", "name": "MCAT", "progress": "68%"},
        {"id": "cars", "name": "CARS", "progress": "82%"},
        {"id": "bio", "name": "Biology", "progress": "41%"}
    ]

    return render_template("dashboard.html", user=user, profile=profile, subjects=subjects)

@app.route("/review/<passage_id>")
def review_passage(passage_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    user_id = user["sub"]
    log_path = USER_DIR / user_id / "user_logs.jsonl"
    question_file = Path("training-data/questions.jsonl")

    if not log_path.exists() or not question_file.exists():
        return "No data available."

    with open(log_path, "r") as f:
        logs = [json.loads(line.strip()) for line in f]

    with open(question_file, "r") as f:
        all_questions = [json.loads(line.strip()) for line in f]

    # Filter for this passage
    reviewed = [
        q for q in all_questions
        if q["passage_id"] == passage_id
        and any(log["question_id"] == q["question_id"] for log in logs)
    ]

    return render_template("review_passage.html", passage_id=passage_id, questions=reviewed)

## Study ROUTE

@app.route("/study", methods=["GET", "POST"])
def start_studying():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    user_id = user["sub"]
    profile_path = USER_DIR / user_id / "user_profile.json"
    question_file = Path("training-data/questions.jsonl")
    passage_file = Path("training-data/passages.jsonl")

    if not profile_path.exists() or not question_file.exists() or not passage_file.exists():
        return "Missing required data files."

    with open(profile_path) as f:
        profile = json.load(f)
    with open(question_file) as f:
        all_questions = [json.loads(line.strip()) for line in f]
    with open(passage_file) as f:
        all_passages = {json.loads(line)["passage_id"]: json.loads(line) for line in f}

    weak = sorted(profile["question_stats"].items(), key=lambda x: x[1]["correct"] / max(x[1]["attempts"], 1))[:2]
    weak_types = [w[0] for w in weak]
    if not weak_types:
        weak_types = ["main idea", "inference"]  # safe default

    questions = []
    for q in all_questions:
        if q["question_type"] in weak_types:
            passage = all_passages.get(q["passage_id"])
            if passage:
                para_idx = q.get("linked_paragraph", 1) - 1
                q["full_passage"] = passage["paragraphs"]  # keep as list for review
                q["passage_title"] = passage["title"]
                q["passage_source"] = passage["journal"]
                questions.append(q)

    session["study_questions"] = questions[:5]
    session["study_index"] = 0
    session["study_answers"] = []
    mode = session.get("feedback_mode", "immediate")

    print("Questions loaded into session:", len(questions[:5]))

    return redirect(url_for("study_question", index=0))


## STUDY START
@app.route("/study/start", methods=["GET", "POST"])
def study_start():
    if request.method == "POST":
        mode = request.form.get("mode")
        session["feedback_mode"] = mode
        return redirect(url_for("start_studying"))
    return render_template("study_mode_select.html")



# Final Review Route 
@app.route("/study/review")
def study_review():
    from log_performance import log_question_performance

    questions = session.get("study_questions", [])
    answers = session.get("study_answers", [])
    meta = session.get("study_answers_meta", [])
    results = []

    for i, q in enumerate(questions):
        selected = answers[i] if i < len(answers) else None
        info = meta[i] if i < len(meta) else {}
        is_correct = selected == q["correct_answer"]
        results.append({
            "question_text": q["question_text"],
            "correct_answer": q["correct_answer"],
            "selected": selected,
            "explanations": q["explanations"],
            "choices": q["choices"],
            "is_correct": is_correct,
            "trap_types": q.get("trap_types"),
            "linked_paragraph": q.get("linked_paragraph"),
            "full_passage": q.get("full_passage", []),
            "time_taken": info.get("time_taken", "-"),
            "confidence": info.get("confidence", "-")
        })

        log_question_performance(
            question_id=q["question_id"],
            question_type=q["question_type"],
            difficulty=q.get("difficulty_rating", 5),
            was_correct=is_correct
        )

    return render_template("study_review.html", results=results)

## APP REVIEW CONFIDENCE
@app.route("/review/confidence/<int:index>", methods=["POST"])
def update_confidence(index):
    confidence = request.form.get("confidence")
    answers_meta = session.get("study_answers_meta", [])
    while len(answers_meta) <= index:
        answers_meta.append({})
    answers_meta[index]["confidence"] = confidence
    session["study_answers_meta"] = answers_meta
    return redirect(url_for("study_review"))


## Study Question timing 
@app.route("/study/question/<int:index>", methods=["GET", "POST"])
def study_question(index):
    questions = session.get("study_questions", [])
    answers = session.get("study_answers", [])
    answers_meta = session.get("study_answers_meta", [])
    mode = session.get("feedback_mode", "immediate")

    if index >= len(questions):
        return redirect(url_for("study_review"))

    if request.method == "POST":
        selected = request.form.get("answer")
        answers.append(selected)

        # Calculate time taken
        start_time = session.pop("time_started", time.time())
        time_taken = round(time.time() - start_time, 2)

        # Save to answer meta
        while len(answers_meta) <= index:
            answers_meta.append({})
        answers_meta[index]["time_taken"] = time_taken

        session["study_answers"] = answers
        session["study_answers_meta"] = answers_meta

        if mode == "immediate":
            return render_template(
                "study_session.html",
                question=questions[index],
                selected=selected,
                index=index,
                mode=mode,
                time_taken=time_taken
            )

        return redirect(url_for("study_question", index=index + 1))

    # GET method: store start time for timing
    session["time_started"] = time.time()

    return render_template(
        "study_session.html",
        question=questions[index],
        selected=None,
        index=index,
        mode=mode
    )


@app.route("/subject/<subject_id>")
def subject_page(subject_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    return render_template("subject_page.html", subject_id=subject_id.capitalize())


@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.userinfo()

    session['user'] = user_info
    save_user_profile(user_info['sub'], user_info['email'], user_info['name'])
    return redirect("/")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect("/")

def save_user_profile(user_id, email, name):
    user_folder = USER_DIR / user_id
    user_folder.mkdir(parents=True, exist_ok=True)
    profile_path = user_folder / "user_profile.json"
    if not profile_path.exists():
        profile_data = {
            "email": email,
            "name": name,
            "question_stats": {},
            "difficulty_stats": {str(i): {"seen": 0, "correct": 0} for i in range(1, 11)},
            "recent_activity": []
        }
        with open(profile_path, "w") as f:
            json.dump(profile_data, f, indent=2)

if __name__ == "__main__":
    app.run(debug=True)
