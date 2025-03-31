from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret")

# Email config
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
mail = Mail(app)

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    if not niche or not platform or not email:
        return {"error": "Missing fields"}, 400

    try:
        prompt = f"Generate 2 viral content ideas for {platform} in the {niche} niche."
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ideas = chat.choices[0].message.content.strip().split("\n")
        session["ideas"] = ideas

        msg = Message("Your Free AI Content Ideas", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return {"message": "Free ideas sent!", "ideas": ideas}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/premium", methods=["POST"])
def premium():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    if not niche or not platform or not email:
        return {"error": "Missing fields"}, 400

    try:
        prompt = f"Generate 6 premium viral content ideas for {platform} in the {niche} niche."
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ideas = chat.choices[0].message.content.strip().split("\n")
        session["ideas"] = ideas

        msg = Message("Your Premium AI Content Ideas", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return {"message": "Premium ideas sent!", "ideas": ideas}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/success")
def success():
    ideas = session.get("ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
