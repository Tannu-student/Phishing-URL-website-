from flask import Flask, render_template, request, jsonify
import pickle
import re
import sqlite3

app = Flask(__name__)

# 🔥 Load model
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
model = pickle.load(open("phishing.pkl", "rb"))

# 🔥 Init DB
def init_db():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        url TEXT,
        prediction TEXT,
        confidence REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# 🔍 Reason function
def get_reasons(url):
    reasons = []

    # Rule-based
    if len(url) > 60:
        reasons.append("URL is very long")

    if url.count('.') > 3:
        reasons.append("Too many subdomains")

    suspicious_words = ["login", "verify", "secure", "account", "update"]
    for word in suspicious_words:
        if word in url.lower():
            reasons.append(f"Contains suspicious word: {word}")

    # Model-based
    try:
        feature_names = vectorizer.get_feature_names_out()
        vec = vectorizer.transform([url])
        coef = model.coef_[0]

        top_indices = vec.toarray()[0].nonzero()[0]

        important_words = sorted(
            [(feature_names[i], coef[i]) for i in top_indices],
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]

        for word, weight in important_words:
            if weight > 0:
                reasons.append(f"Word '{word}' increases phishing risk")
    except:
        pass

    return reasons


# 🧠 Attack Type Detection
def detect_attack_type(url):
    url = url.lower()

    if any(word in url for word in ["bank", "account", "credit", "debit"]):
        return "💳 Banking Scam"
    elif any(word in url for word in ["instagram", "facebook", "login", "signin"]):
        return "📱 Social Media Hack"
    elif any(word in url for word in ["job", "career", "hiring", "offer"]):
        return "💼 Fake Job Scam"
    elif any(word in url for word in ["otp", "verify", "verification", "secure"]):
        return "🔐 OTP / Verification Scam"
    else:
        return "⚠️ General Phishing"


# 💾 Save to DB
def save_result(url, prediction, confidence):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO history (url, prediction, confidence) VALUES (?, ?, ?)",
        (url, prediction, confidence)
    )

    conn.commit()
    conn.close()


# 🌐 MAIN ROUTE
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    predict = None
    reasons = None
    attack_type = None
    url = None
    confidence = None

    if request.method == "POST":
        url = request.form["url"]

        cleaned_url = re.sub(r'^https?://(www\.)?', '', url)

        vec = vectorizer.transform([cleaned_url])
        result = model.predict(vec)[0]
        confidence = max(model.predict_proba(vec)[0]) * 100

        # Attack type
        if result == "bad":
            attack_type = detect_attack_type(cleaned_url)

        # Prediction text
        if result == "bad":
            predict = "⚠️ Phishing Website Detected"
        else:
            predict = "✅ Safe Website"

        # Reasons
        reasons = get_reasons(cleaned_url)

        # Save history
        save_result(url, predict, confidence)

        return render_template(
            "index.html",
            predict=predict,
            reasons=reasons,
            url=url,
            attack_type=attack_type
        )

    return render_template("index.html")


# 🚀 API ROUTE
@app.route("/predict", methods=["POST"])
def predict_api():
    data = request.json
    url = data["url"]

    cleaned_url = re.sub(r'^https?://(www\.)?', '', url)

    vec = vectorizer.transform([cleaned_url])
    result = model.predict(vec)[0]
    confidence = max(model.predict_proba(vec)[0]) * 100

    if result == "bad":
        prediction_text = "Phishing"
        attack_type = detect_attack_type(cleaned_url)
    else:
        prediction_text = "Safe"
        attack_type = None

    reasons = get_reasons(cleaned_url)

    save_result(url, prediction_text, confidence)

    return jsonify({
        "prediction": prediction_text,
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "attack_type": attack_type
    })


# 📜 HISTORY
@app.route("/history")
def history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()

    c.execute("SELECT url, prediction FROM history ORDER BY ROWID DESC")
    data = c.fetchall()

    conn.close()
    return jsonify(data)


# 🗑 CLEAR HISTORY
@app.route("/clear_history", methods=["POST"])
def clear_history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()

    c.execute("DELETE FROM history")

    conn.commit()
    conn.close()

    return {"status": "cleared"}


# ▶ RUN
if __name__ == "__main__":
    app.run(debug=True)