from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# OpenAI v1.x client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask-Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")

mail = Mail(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_ideas():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")
    is_premium = data.get("premium", False)

    if not niche or not platform or not email:
        return jsonify({"error": "Missing required fields"}), 400

    idea_count = 6 if is_premium else 2

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate {idea_count} viral content ideas for {platform} in the {niche} niche."
                }
            ]
        )
        raw_ideas = completion.choices[0].message.content.strip()
        ideas = [idea.strip("- ").strip() for idea in raw_ideas.split("\n") if idea.strip()]

        # Store ideas in session for success page
        session["generated_ideas"] = ideas

        # Send email
        msg = Message("Your AI-Generated Content Ideas", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return jsonify({"message": "Email sent!", "ideas": ideas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    ideas = session.get("generated_ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
