from flask import Flask, render_template, request, jsonify, session
from flask_mail import Mail, Message
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask-Mail config (Gmail SMTP)
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
    try:
        data = request.get_json()
        niche = data.get("niche")
        platform = data.get("platform")
        email = data.get("email")

        if not niche or not platform or not email:
            return jsonify({"error": "Missing required fields"}), 400

        # Generate ideas using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates viral content ideas."
                },
                {
                    "role": "user",
                    "content": f"Generate 5 viral content ideas for {platform} in the {niche} niche."
                }
            ]
        )

        ideas_raw = response.choices[0].message["content"]
        ideas = [line.strip("- ").strip() for line in ideas_raw.strip().split("\n") if line.strip()]
        session["generated_ideas"] = ideas

        # Send email with ideas
        message = Message(
            "Your AI-Generated Content Ideas",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )
        message.body = "\n".join(ideas)
        mail.send(message)

        return jsonify({"message": "Email sent!", "ideas": ideas})
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@app.route("/success")
def success():
    ideas = session.get("generated_ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
